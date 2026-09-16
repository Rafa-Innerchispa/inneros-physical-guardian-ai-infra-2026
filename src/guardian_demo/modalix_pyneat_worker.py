"""Persistent target-side PyNeat worker used by the Guardian SSH bridge.

The host sends this module to the already-provisioned Modalix Python runtime as
an in-memory ``python -c`` program. One bounded SSH session builds the model
exactly once, then accepts length-prefixed metadata plus raw image bytes for
multiple frames. Frames are never written and stdout contains only NDJSON.
"""

from __future__ import annotations

COCO80_LABELS = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
)

WORKER_SCHEMA = "inneros.guardian.sima.modalix-worker.v2"
DECODE_METHOD = "YOLO26_ANCHOR_FREE_LTRB_SIGMOID_COCO80_CLASS_AWARE_NMS_V1"
WIRE_PROTOCOL = "GUARDIAN_LENGTH_PREFIXED_METADATA_IMAGE_V1"
MAX_ENVELOPE_BYTES = 1_100_000
MAX_HEADER_BYTES = 32_000
EXPECTED_OUTPUT_SHAPES = (
    (80, 80, 4),
    (40, 40, 4),
    (20, 20, 4),
    (80, 80, 80),
    (40, 40, 80),
    (20, 20, 80),
    (80, 80, 32),
    (40, 40, 32),
    (20, 20, 32),
    (160, 160, 32),
)


def _sha256_file(path: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tensor_to_numpy(tensor, np):
    """Use the accessor proven on pyneat._pyneat_core.Tensor 0.4.0."""

    converter = getattr(tensor, "to_numpy", None)
    if not callable(converter):
        raise RuntimeError("PyNeat output tensor does not expose to_numpy()")
    array = np.asarray(converter(), dtype=np.float32)
    if array.ndim == 4 and array.shape[0] == 1:
        array = array[0]
    if not array.flags.c_contiguous:
        array = np.ascontiguousarray(array)
    return array


def _class_aware_nms(boxes, scores, class_ids, np, *, iou_threshold: float, max_det: int):
    if boxes.shape[0] == 0:
        return []
    offsets = class_ids.astype(np.float32)[:, None] * 4096.0
    nms_boxes = boxes + offsets
    order = np.argsort(scores)[::-1]
    kept: list[int] = []
    while order.size and len(kept) < max_det:
        current = int(order[0])
        kept.append(current)
        if order.size == 1:
            break
        remaining = order[1:]
        left = np.maximum(nms_boxes[current, 0], nms_boxes[remaining, 0])
        top = np.maximum(nms_boxes[current, 1], nms_boxes[remaining, 1])
        right = np.minimum(nms_boxes[current, 2], nms_boxes[remaining, 2])
        bottom = np.minimum(nms_boxes[current, 3], nms_boxes[remaining, 3])
        intersection = np.maximum(0.0, right - left) * np.maximum(0.0, bottom - top)
        current_area = max(
            0.0,
            float(nms_boxes[current, 2] - nms_boxes[current, 0]),
        ) * max(0.0, float(nms_boxes[current, 3] - nms_boxes[current, 1]))
        other_areas = np.maximum(0.0, nms_boxes[remaining, 2] - nms_boxes[remaining, 0]) * np.maximum(
            0.0,
            nms_boxes[remaining, 3] - nms_boxes[remaining, 1],
        )
        union = current_area + other_areas - intersection
        iou = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
        order = remaining[iou <= iou_threshold]
    return kept


def decode_yolo26m_heads(
    outputs,
    np,
    *,
    confidence_floor: float,
    iou_threshold: float,
    pre_nms_top_k: int,
    post_nms_top_k: int,
):
    """Decode the exact ten-head contract proven on the Modalix target."""

    if len(outputs) != len(EXPECTED_OUTPUT_SHAPES):
        raise RuntimeError("Modalix runner did not return the required ten output tensors")
    observed_shapes = tuple(tuple(int(value) for value in output.shape) for output in outputs)
    if observed_shapes != EXPECTED_OUTPUT_SHAPES:
        raise RuntimeError(f"unexpected Modalix output tensor shapes: {observed_shapes}")

    candidate_boxes = []
    candidate_scores = []
    candidate_classes = []
    for head_index, stride in enumerate((8, 16, 32)):
        box_head = outputs[head_index]
        class_head = outputs[head_index + 3]
        height, width, _ = box_head.shape
        grid_y, grid_x = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
        center_x = (grid_x + 0.5) * stride
        center_y = (grid_y + 0.5) * stride
        x1 = np.clip(center_x - box_head[..., 0] * stride, 0.0, 640.0)
        y1 = np.clip(center_y - box_head[..., 1] * stride, 0.0, 640.0)
        x2 = np.clip(center_x + box_head[..., 2] * stride, 0.0, 640.0)
        y2 = np.clip(center_y + box_head[..., 3] * stride, 0.0, 640.0)
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(class_head, -25.0, 25.0)))
        scores = np.max(probabilities, axis=-1)
        class_ids = np.argmax(probabilities, axis=-1)
        selected = scores >= confidence_floor
        if np.any(selected):
            boxes = np.stack((x1[selected], y1[selected], x2[selected], y2[selected]), axis=-1)
            selected_scores = scores[selected]
            selected_classes = class_ids[selected]
            finite = np.isfinite(boxes).all(axis=1) & np.isfinite(selected_scores)
            positive = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])
            keep = finite & positive
            if np.any(keep):
                candidate_boxes.append(boxes[keep].astype(np.float32, copy=False))
                candidate_scores.append(selected_scores[keep].astype(np.float32, copy=False))
                candidate_classes.append(selected_classes[keep].astype(np.int64, copy=False))

    if not candidate_boxes:
        return []
    boxes = np.concatenate(candidate_boxes, axis=0)
    scores = np.concatenate(candidate_scores, axis=0)
    class_ids = np.concatenate(candidate_classes, axis=0)
    order = np.argsort(scores)[::-1][:pre_nms_top_k]
    boxes, scores, class_ids = boxes[order], scores[order], class_ids[order]
    kept = _class_aware_nms(
        boxes,
        scores,
        class_ids,
        np,
        iou_threshold=iou_threshold,
        max_det=post_nms_top_k,
    )

    detections = []
    for index in kept:
        class_id = int(class_ids[index])
        if not 0 <= class_id < len(COCO80_LABELS):
            raise RuntimeError(f"decoded class id is outside COCO80: {class_id}")
        bbox = boxes[index]
        detections.append(
            {
                "class_id": class_id,
                "label": COCO80_LABELS[class_id],
                "confidence": round(float(scores[index]), 6),
                "bbox": [round(float(value / 640.0), 6) for value in bbox],
                "bbox_xyxy": [round(float(value), 3) for value in bbox],
            }
        )
    return detections


def _main() -> None:
    import base64
    import contextlib
    import hashlib
    import io
    import json
    import os
    import platform
    import sys
    import time
    from datetime import datetime, timezone

    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    if not isinstance(request, dict):
        raise ValueError("worker request must be a JSON object")
    operation = request.get("operation", "infer")
    model_archive = request.get("model_archive")
    if not isinstance(model_archive, str) or not model_archive.startswith("/media/nvme/models/"):
        raise ValueError("worker model archive is not allowlisted")
    if not model_archive.endswith(".tar.gz") or not os.path.isfile(model_archive):
        raise FileNotFoundError("worker model archive is unavailable")
    expected_model_sha256 = request.get("expected_model_sha256")
    observed_model_sha256 = _sha256_file(model_archive)
    if observed_model_sha256 != expected_model_sha256:
        raise RuntimeError("Modalix model archive SHA-256 mismatch")

    import pyneat  # type: ignore

    runtime_version = str(getattr(pyneat, "__version__", "unknown"))
    if runtime_version == "unknown":
        try:
            from importlib.metadata import version

            runtime_version = version("pyneat")
        except Exception:
            pass
    if operation == "health":
        print(
            json.dumps(
                {
                    "worker_schema": WORKER_SCHEMA,
                    "operation": "health",
                    "runtime_version": runtime_version,
                    "machine": platform.machine(),
                    "model_sha256": observed_model_sha256,
                },
                separators=(",", ":"),
            )
        )
        return
    if operation != "infer":
        raise ValueError("unsupported worker operation")

    import cv2  # type: ignore
    import numpy as np

    image_encoded = request.get("image_base64")
    if not isinstance(image_encoded, str) or not image_encoded:
        raise ValueError("worker request is missing image bytes")
    image_bytes = base64.b64decode(image_encoded, validate=True)
    source_sha256 = hashlib.sha256(image_bytes).hexdigest()
    if source_sha256 != request.get("source_sha256"):
        raise RuntimeError("worker source SHA-256 mismatch")

    preprocess_started = time.perf_counter()
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("worker could not decode a three-channel image")
    if int(image.shape[1]) != request.get("width") or int(image.shape[0]) != request.get("height"):
        raise RuntimeError("worker decoded dimensions do not match the submitted frame")
    if image.shape[:2] != (640, 640):
        image = cv2.resize(image, (640, 640), interpolation=cv2.INTER_LINEAR)
    image_f32 = np.ascontiguousarray(image.astype(np.float32) / 255.0)
    preprocess_ms = (time.perf_counter() - preprocess_started) * 1000.0

    runtime_logs = io.StringIO()
    with contextlib.redirect_stdout(runtime_logs), contextlib.redirect_stderr(runtime_logs):
        build_started = time.perf_counter()
        runner = pyneat.Model(model_archive).build()
        model_build_ms = (time.perf_counter() - build_started) * 1000.0
        tensor = pyneat.Tensor.from_numpy(image_f32)
        inference_started = time.perf_counter()
        raw_outputs = runner.run([tensor])
        mla_inference_ms = (time.perf_counter() - inference_started) * 1000.0

    arrays = [_tensor_to_numpy(output, np) for output in raw_outputs]
    raw_digest = hashlib.sha256()
    for array in arrays:
        raw_digest.update(str(tuple(int(value) for value in array.shape)).encode("ascii"))
        raw_digest.update(array.tobytes(order="C"))
    decode_started = time.perf_counter()
    detections = decode_yolo26m_heads(
        arrays,
        np,
        confidence_floor=float(request.get("confidence_floor", 0.0001)),
        iou_threshold=float(request.get("nms_iou_threshold", 0.45)),
        pre_nms_top_k=int(request.get("pre_nms_top_k", 300)),
        post_nms_top_k=int(request.get("post_nms_top_k", 100)),
    )
    decode_ms = (time.perf_counter() - decode_started) * 1000.0
    response = {
        "worker_schema": WORKER_SCHEMA,
        "operation": "infer",
        "execution_status": "REAL_TARGET_MLA_DECODE_SUCCESS",
        "request_nonce": request.get("request_nonce"),
        "frame_id": request.get("frame_id"),
        "source_id": request.get("source_id"),
        "source_sha256": source_sha256,
        "inferred_at": datetime.now(timezone.utc).isoformat(),
        "runtime_version": runtime_version,
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "model_sha256": observed_model_sha256,
        "model_build_ms": round(model_build_ms, 3),
        "preprocessing_ms": round(preprocess_ms, 3),
        "mla_inference_ms": round(mla_inference_ms, 3),
        "decode_ms": round(decode_ms, 3),
        "output_tensor_count": len(arrays),
        "output_tensor_shapes": [list(array.shape) for array in arrays],
        "raw_output_sha256": raw_digest.hexdigest(),
        "decode_method": DECODE_METHOD,
        "confidence_floor": float(request.get("confidence_floor", 0.0001)),
        "policy_confidence_threshold": float(request.get("policy_confidence_threshold", 0.25)),
        "nms_iou_threshold": float(request.get("nms_iou_threshold", 0.45)),
        "pre_nms_top_k": int(request.get("pre_nms_top_k", 300)),
        "post_nms_top_k": int(request.get("post_nms_top_k", 100)),
        "detections": detections,
    }
    print(json.dumps(response, separators=(",", ":")))


def _read_exact(stream, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            raise EOFError("worker input ended inside a framed request")
        chunks.extend(chunk)
    return bytes(chunks)


def _read_envelope(stream, json_module, struct_module):
    prefix = stream.read(4)
    if not prefix:
        return None
    if len(prefix) != 4:
        raise EOFError("worker input ended inside the envelope prefix")
    envelope_size = struct_module.unpack(">I", prefix)[0]
    if envelope_size == 0:
        return None
    if envelope_size < 4 or envelope_size > MAX_ENVELOPE_BYTES:
        raise ValueError("worker envelope size is outside the bounded contract")
    envelope = _read_exact(stream, envelope_size)
    header_size = struct_module.unpack(">I", envelope[:4])[0]
    if header_size <= 0 or header_size > MAX_HEADER_BYTES or 4 + header_size > len(envelope):
        raise ValueError("worker metadata size is outside the bounded contract")
    header = json_module.loads(envelope[4 : 4 + header_size].decode("utf-8"))
    if not isinstance(header, dict):
        raise ValueError("worker metadata must be a JSON object")
    image_bytes = envelope[4 + header_size :]
    image_size = header.get("image_size", 0)
    if isinstance(image_size, bool) or not isinstance(image_size, int) or image_size != len(image_bytes):
        raise ValueError("worker image length does not match its metadata")
    return header, image_bytes


def _write_response(stream, json_module, response) -> None:
    encoded = json_module.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n"
    stream.write(encoded)
    stream.flush()


def _run_warm_inference(request, image_bytes, state, modules):
    contextlib, hashlib, io, platform, time, datetime, timezone = modules
    runner = state["runner"]
    np = state["np"]
    cv2 = state["cv2"]
    pyneat = state["pyneat"]
    if not image_bytes:
        raise ValueError("worker request is missing image bytes")
    source_sha256 = hashlib.sha256(image_bytes).hexdigest()
    if source_sha256 != request.get("source_sha256"):
        raise RuntimeError("worker source SHA-256 mismatch")

    preprocess_started = time.perf_counter()
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("worker could not decode a three-channel image")
    if int(image.shape[1]) != request.get("width") or int(image.shape[0]) != request.get("height"):
        raise RuntimeError("worker decoded dimensions do not match the submitted frame")
    if image.shape[:2] != (640, 640):
        image = cv2.resize(image, (640, 640), interpolation=cv2.INTER_LINEAR)
    image_f32 = np.ascontiguousarray(image.astype(np.float32) / 255.0)
    preprocess_ms = (time.perf_counter() - preprocess_started) * 1000.0

    runtime_logs = io.StringIO()
    with contextlib.redirect_stdout(runtime_logs), contextlib.redirect_stderr(runtime_logs):
        tensor = pyneat.Tensor.from_numpy(image_f32)
        inference_started = time.perf_counter()
        raw_outputs = runner.run([tensor])
        mla_inference_ms = (time.perf_counter() - inference_started) * 1000.0

    arrays = [_tensor_to_numpy(output, np) for output in raw_outputs]
    raw_digest = hashlib.sha256()
    for array in arrays:
        raw_digest.update(str(tuple(int(value) for value in array.shape)).encode("ascii"))
        raw_digest.update(array.tobytes(order="C"))
    decode_started = time.perf_counter()
    detections = decode_yolo26m_heads(
        arrays,
        np,
        confidence_floor=float(request.get("confidence_floor", 0.0001)),
        iou_threshold=float(request.get("nms_iou_threshold", 0.45)),
        pre_nms_top_k=int(request.get("pre_nms_top_k", 300)),
        post_nms_top_k=int(request.get("post_nms_top_k", 100)),
    )
    decode_ms = (time.perf_counter() - decode_started) * 1000.0
    return {
        "worker_schema": WORKER_SCHEMA,
        "operation": "infer",
        "execution_status": "REAL_TARGET_MLA_DECODE_SUCCESS",
        "wire_protocol": WIRE_PROTOCOL,
        "worker_instance_id": state["worker_instance_id"],
        "model_load_count": 1,
        "model_rebuilt_for_frame": False,
        "request_sequence": state["request_sequence"],
        "request_nonce": request.get("request_nonce"),
        "frame_id": request.get("frame_id"),
        "source_id": request.get("source_id"),
        "source_sha256": source_sha256,
        "inferred_at": datetime.now(timezone.utc).isoformat(),
        "runtime_version": state["runtime_version"],
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "model_sha256": state["model_sha256"],
        "worker_startup_model_build_ms": round(float(state["model_build_ms"]), 3),
        "preprocessing_ms": round(preprocess_ms, 3),
        "mla_inference_ms": round(mla_inference_ms, 3),
        "decode_ms": round(decode_ms, 3),
        "output_tensor_count": len(arrays),
        "output_tensor_shapes": [list(array.shape) for array in arrays],
        "raw_output_sha256": raw_digest.hexdigest(),
        "decode_method": DECODE_METHOD,
        "confidence_floor": float(request.get("confidence_floor", 0.0001)),
        "policy_confidence_threshold": float(request.get("policy_confidence_threshold", 0.25)),
        "nms_iou_threshold": float(request.get("nms_iou_threshold", 0.45)),
        "pre_nms_top_k": int(request.get("pre_nms_top_k", 300)),
        "post_nms_top_k": int(request.get("post_nms_top_k", 100)),
        "detections": detections,
    }


def _persistent_main() -> None:
    import contextlib
    import hashlib
    import io
    import json
    import os
    import platform
    import secrets
    import struct
    import sys
    import time
    from datetime import datetime, timezone

    state = {
        "runner": None,
        "np": None,
        "cv2": None,
        "pyneat": None,
        "runtime_version": None,
        "model_sha256": None,
        "model_build_ms": None,
        "worker_instance_id": "modalix-worker-" + secrets.token_hex(12),
        "request_sequence": 0,
    }
    modules = (contextlib, hashlib, io, platform, time, datetime, timezone)

    while True:
        try:
            envelope = _read_envelope(sys.stdin.buffer, json, struct)
        except Exception as exc:
            _write_response(
                sys.stdout.buffer,
                json,
                {
                    "worker_schema": WORKER_SCHEMA,
                    "operation": "protocol",
                    "execution_status": "BLOCKED",
                    "error_code": "MALFORMED_WORKER_ENVELOPE",
                    "error": str(exc)[:160],
                    "worker_instance_id": state["worker_instance_id"],
                    "model_load_count": 1 if state["runner"] is not None else 0,
                },
            )
            return
        if envelope is None:
            return
        request, image_bytes = envelope
        operation = request.get("operation")

        if operation == "initialize":
            try:
                if image_bytes:
                    raise ValueError("worker initialization cannot include image bytes")
                model_archive = request.get("model_archive")
                if not isinstance(model_archive, str) or not model_archive.startswith("/media/nvme/models/"):
                    raise ValueError("worker model archive is not allowlisted")
                if not model_archive.endswith(".tar.gz") or not os.path.isfile(model_archive):
                    raise FileNotFoundError("worker model archive is unavailable")
                expected_model_sha256 = request.get("expected_model_sha256")
                if state["runner"] is None:
                    observed_model_sha256 = _sha256_file(model_archive)
                    if observed_model_sha256 != expected_model_sha256:
                        raise RuntimeError("Modalix model archive SHA-256 mismatch")
                    import os
                    os.environ["SIMA_ALLOW_INPUTSTREAM_CPU_TO_EV74_COPY"] = "1"
                    import cv2  # type: ignore
                    import numpy as np
                    import pyneat  # type: ignore

                    runtime_version = str(getattr(pyneat, "__version__", "unknown"))
                    if runtime_version == "unknown":
                        try:
                            from importlib.metadata import version

                            runtime_version = version("pyneat")
                        except Exception:
                            pass
                    runtime_logs = io.StringIO()
                    with contextlib.redirect_stdout(runtime_logs), contextlib.redirect_stderr(runtime_logs):
                        build_started = time.perf_counter()
                        runner = pyneat.Model(model_archive).build()
                        model_build_ms = (time.perf_counter() - build_started) * 1000.0
                    state.update(
                        runner=runner,
                        np=np,
                        cv2=cv2,
                        pyneat=pyneat,
                        runtime_version=runtime_version,
                        model_sha256=observed_model_sha256,
                        model_build_ms=model_build_ms,
                    )
                elif expected_model_sha256 != state["model_sha256"]:
                    raise RuntimeError("worker cannot switch models inside a warm session")
                _write_response(
                    sys.stdout.buffer,
                    json,
                    {
                        "worker_schema": WORKER_SCHEMA,
                        "operation": "initialize",
                        "execution_status": "WORKER_READY",
                        "wire_protocol": WIRE_PROTOCOL,
                        "worker_instance_id": state["worker_instance_id"],
                        "runtime_version": state["runtime_version"],
                        "machine": platform.machine(),
                        "model_sha256": state["model_sha256"],
                        "model_load_count": 1,
                        "model_build_ms": round(float(state["model_build_ms"]), 3),
                    },
                )
            except Exception as exc:
                _write_response(
                    sys.stdout.buffer,
                    json,
                    {
                        "worker_schema": WORKER_SCHEMA,
                        "operation": "initialize",
                        "execution_status": "BLOCKED",
                        "error_code": "WORKER_INITIALIZATION_FAILED",
                        "error": str(exc)[:160],
                        "worker_instance_id": state["worker_instance_id"],
                        "model_load_count": 0,
                    },
                )
                return
            continue

        state["request_sequence"] += 1
        try:
            if operation != "infer":
                raise ValueError("unsupported worker operation")
            if state["runner"] is None:
                raise RuntimeError("worker has not completed model initialization")
            response = _run_warm_inference(request, image_bytes, state, modules)
        except Exception as exc:
            message = str(exc)
            error_code = "FRAME_INFERENCE_FAILED"
            if "decode a three-channel image" in message:
                error_code = "IMAGE_DECODE_FAILED"
            elif "SHA-256 mismatch" in message:
                error_code = "SOURCE_HASH_MISMATCH"
            elif "dimensions" in message:
                error_code = "SOURCE_DIMENSIONS_MISMATCH"
            response = {
                "worker_schema": WORKER_SCHEMA,
                "operation": "infer",
                "execution_status": "BLOCKED",
                "wire_protocol": WIRE_PROTOCOL,
                "error_code": error_code,
                "error": message[:160],
                "worker_instance_id": state["worker_instance_id"],
                "model_load_count": 1 if state["runner"] is not None else 0,
                "model_rebuilt_for_frame": False,
                "request_sequence": state["request_sequence"],
                "request_nonce": request.get("request_nonce"),
                "frame_id": request.get("frame_id"),
                "source_id": request.get("source_id"),
                "source_sha256": request.get("source_sha256"),
            }
        _write_response(sys.stdout.buffer, json, response)


if __name__ == "__main__":
    try:
        _persistent_main()
    except Exception as exc:  # fail closed without dumping frame/request contents
        import sys

        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
