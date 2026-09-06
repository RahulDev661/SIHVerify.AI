import cv2
import numpy as np
import math


# ============================================================
# STAMP / SEAL TAMPERING DETECTOR
# ============================================================
#
# Pipeline:
#   1. Detect circular candidates
#   2. Estimate whether each candidate looks like a stamp
#   3. Merge overlapping detections belonging to the same stamp
#   4. Analyze local texture / ink / boundary consistency
#   5. Produce an explainable tamper score
#
# This is a prototype forensic heuristic.
# It should be treated as a screening signal, not a final
# authenticity decision.
# ============================================================


# -----------------------------
# Configuration
# -----------------------------

MIN_STAMP_LIKELIHOOD = 0.25

REVIEW_THRESHOLD = 25.0
SUSPICIOUS_THRESHOLD = 55.0

# Tampering signal weights
COLOR_WEIGHT = 5.0
BOUNDARY_WEIGHT = 60.0
TEXTURE_WEIGHT = 20.0
RECT_SEAM_WEIGHT = 30.0


# ============================================================
# BASIC UTILITIES
# ============================================================

def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


def _safe_std(values):
    if values is None or len(values) == 0:
        return 0.0

    return float(np.std(values))


def _circle_bbox(x, y, r, width, height):
    x1 = max(0, int(x - r))
    y1 = max(0, int(y - r))
    x2 = min(width, int(x + r))
    y2 = min(height, int(y + r))

    return x1, y1, x2, y2


def _circle_mask(shape, x, y, r):
    mask = np.zeros(shape[:2], dtype=np.uint8)

    cv2.circle(
        mask,
        (int(x), int(y)),
        max(1, int(r)),
        255,
        -1
    )

    return mask


# ============================================================
# CIRCLE DETECTION
# ============================================================

def _detect_circles(image):
    """
    Detect circular structures using Hough Circle Transform.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (5, 5), 1.2)

    h, w = gray.shape

    min_dim = min(h, w)

    min_radius = max(20, int(min_dim * 0.015))
    max_radius = max(min_radius + 5, int(min_dim * 0.20))

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(30, int(min_dim * 0.035)),
        param1=100,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is None:
        return []

    circles = np.round(circles[0]).astype(int)

    return [
        (int(x), int(y), int(r))
        for x, y, r in circles
        if r > 0
    ]


# ============================================================
# STAGE 0 - CIRCLE NMS
# ============================================================

def _nms_circles(circles):
    """
    Remove obvious duplicate Hough detections.

    This is intentionally conservative because a single
    physical stamp may still generate several circles.
    Those will be merged later after stamp-likelihood analysis.
    """

    circles = sorted(
        circles,
        key=lambda c: c[2],
        reverse=True
    )

    kept = []

    for circle in circles:

        x, y, r = circle

        duplicate = False

        for kx, ky, kr in kept:

            distance = math.hypot(
                x - kx,
                y - ky
            )

            # Strong duplicate condition
            if distance < 0.55 * max(r, kr):

                duplicate = True
                break

            # Contained circle
            if distance + min(r, kr) < max(r, kr) * 0.75:

                duplicate = True
                break

        if not duplicate:
            kept.append(circle)

    return kept


# ============================================================
# STAGE 1 - STAMP LIKELIHOOD
# ============================================================

def _stamp_likelihood(image, circle):
    """
    Estimate whether a detected circle looks like a stamp/seal.

    Signals:
      - color/saturation
      - coverage
      - boundary strength
      - local contrast
    """

    h, w = image.shape[:2]

    x, y, r = circle

    if r <= 5:
        return 0.0

    x1, y1, x2, y2 = _circle_bbox(
        x,
        y,
        r,
        w,
        h
    )

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return 0.0

    hsv = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
    )

    saturation = hsv[:, :, 1]

    # --------------------------------------------------------
    # Saturation
    # --------------------------------------------------------

    sat_mean = float(np.mean(saturation))

    saturation_score = _clamp(
        (sat_mean - 15.0) / 90.0
    )

    # --------------------------------------------------------
    # Colored pixel coverage
    # --------------------------------------------------------

    colored_pixels = np.sum(
        saturation > 35
    )

    total_pixels = saturation.size

    coverage = (
        colored_pixels / total_pixels
        if total_pixels > 0
        else 0.0
    )

    coverage_score = _clamp(
        coverage / 0.35
    )

    # --------------------------------------------------------
    # Boundary
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        60,
        140
    )

    edge_ratio = np.mean(
        edges > 0
    )

    boundary_score = _clamp(
        edge_ratio / 0.15
    )

    # --------------------------------------------------------
    # Local contrast
    # --------------------------------------------------------

    contrast = float(
        np.std(gray)
    )

    contrast_score = _clamp(
        contrast / 70.0
    )

    # --------------------------------------------------------
    # Final likelihood
    # --------------------------------------------------------

    likelihood = (
        0.35 * saturation_score
        + 0.25 * coverage_score
        + 0.20 * boundary_score
        + 0.20 * contrast_score
    )

    return round(
        float(likelihood),
        3
    )


# ============================================================
# STAMP REGION MERGING
# ============================================================

def _circle_overlap_ratio(c1, c2):
    """
    Approximate overlap using bounding boxes.

    Returns:
        0.0 - 1.0
    """

    x1, y1, r1 = c1
    x2, y2, r2 = c2

    ax1 = x1 - r1
    ay1 = y1 - r1
    ax2 = x1 + r1
    ay2 = y1 + r1

    bx1 = x2 - r2
    by1 = y2 - r2
    bx2 = x2 + r2
    by2 = y2 + r2

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    intersection = (
        (ix2 - ix1)
        * (iy2 - iy1)
    )

    area_a = max(
        1,
        (ax2 - ax1)
        * (ay2 - ay1)
    )

    area_b = max(
        1,
        (bx2 - bx1)
        * (by2 - by1)
    )

    return intersection / min(
        area_a,
        area_b
    )


def _should_merge(c1, c2):
    """
    Decide whether two likely stamp detections belong
    to the same physical stamp.
    """

    x1, y1, r1 = c1
    x2, y2, r2 = c2

    distance = math.hypot(
        x1 - x2,
        y1 - y2
    )

    # --------------------------------------------------------
    # Close centers
    # --------------------------------------------------------

    if distance <= 0.65 * (r1 + r2):
        return True

    # --------------------------------------------------------
    # Significant bounding-box overlap
    # --------------------------------------------------------

    overlap = _circle_overlap_ratio(
        c1,
        c2
    )

    if overlap >= 0.20:
        return True

    # --------------------------------------------------------
    # One circle is substantially inside another
    # --------------------------------------------------------

    if distance + min(r1, r2) <= max(r1, r2) * 1.05:
        return True

    return False


def _merge_stamp_candidates(candidates):
    """
    Group multiple Hough detections belonging to the same
    physical stamp.

    candidates:
        [
            {
                "circle": (x, y, r),
                "stamp_likelihood": float
            }
        ]
    """

    if not candidates:
        return []

    groups = []

    # --------------------------------------------------------
    # Build connected groups
    # --------------------------------------------------------

    for candidate in candidates:

        circle = candidate["circle"]

        matching_groups = []

        for group_index, group in enumerate(groups):

            for existing in group:

                if _should_merge(
                    circle,
                    existing["circle"]
                ):
                    matching_groups.append(
                        group_index
                    )
                    break

        if not matching_groups:

            groups.append(
                [candidate]
            )

        else:

            # Add to first matching group
            target = matching_groups[0]

            groups[target].append(
                candidate
            )

            # Merge any other connected groups
            for index in reversed(
                matching_groups[1:]
            ):

                groups[target].extend(
                    groups[index]
                )

                del groups[index]

    # --------------------------------------------------------
    # Convert each group to one representative
    # --------------------------------------------------------

    merged = []

    for group in groups:

        # Select the strongest candidate
        # by stamp likelihood, then radius.
        best = max(
            group,
            key=lambda item: (
                1 if item.get("color_component", False) else 0,
                item["stamp_likelihood"],
                item["circle"][2]
            )
        )

        bx, by, br = best["circle"]

        # Use a weighted center to make the final
        # region more stable.
        weights = np.array(
            [
                max(
                    0.1,
                    item["stamp_likelihood"]
                )
                for item in group
            ],
            dtype=np.float32
        )

        xs = np.array(
            [
                item["circle"][0]
                for item in group
            ],
            dtype=np.float32
        )

        ys = np.array(
            [
                item["circle"][1]
                for item in group
            ],
            dtype=np.float32
        )

        rs = np.array(
            [
                item["circle"][2]
                for item in group
            ],
            dtype=np.float32
        )

        center_x = int(
            np.average(
                xs,
                weights=weights
            )
        )

        center_y = int(
            np.average(
                ys,
                weights=weights
            )
        )

        # Radius should cover the detected stamp
        # without becoming excessively large.
        radius = int(
            max(
                br,
                np.max(
                    np.sqrt(
                        (xs - center_x) ** 2
                        + (ys - center_y) ** 2
                    )
                    + rs * 0.75
                )
            )
        )

        radius = int(
            min(
                radius,
                br * 1.45
            )
        )

        # When a color-ink component is present, its geometry is a stronger
        # estimate of the actual stamp footprint than the weighted Hough
        # centers. Preserve that geometry exactly.
        color_members = [
            item for item in group
            if item.get("color_component", False)
        ]
        if color_members:
            color_best = max(
                color_members,
                key=lambda item: item["circle"][2]
            )
            center_x, center_y, radius = color_best["circle"]

        merged.append(
            {
                "circle": (
                    center_x,
                    center_y,
                    radius
                ),
                "stamp_likelihood": round(
                    max(
                        item["stamp_likelihood"]
                        for item in group
                    ),
                    3
                ),
                "candidate_count": len(group),
                "color_component": any(
                    item.get("color_component", False)
                    for item in group
                )
            }
        )

    return merged


# ============================================================
# COLOR / INK ANALYSIS
# ============================================================

def _analyze_color(image, x, y, r):
    """
    Analyze hue consistency inside the stamp.
    """

    h, w = image.shape[:2]

    x1, y1, x2, y2 = _circle_bbox(
        x,
        y,
        r,
        w,
        h
    )

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return 0.0, []

    hsv = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
    )

    saturation = hsv[:, :, 1]
    hue = hsv[:, :, 0]

    ink_mask = saturation > 40

    ink_hues = hue[ink_mask]

    if len(ink_hues) < 20:
        return 0.0, []

    hue_std = _safe_std(
        ink_hues
    )

    reasons = []

    # Raised threshold to reduce false positives
    # on normal multi-color / anti-aliased stamps.
    if hue_std > 35:

        reasons.append(
            "Ink hue variation is unusually high "
            f"(std={hue_std:.1f}), which may indicate "
            "mixed ink sources or compositing."
        )

    # Normalize anomaly.
    anomaly = _clamp(
        (hue_std - 20.0) / 60.0
    )

    return anomaly, reasons


# ============================================================
# LOCAL TEXTURE ANALYSIS
# ============================================================

def _analyze_local_texture(image, x, y, r):
    """
    Compare texture/noise inside the stamp against the
    immediately surrounding document.

    This is one of the strongest indicators for synthetic
    test tampering such as:
        - smoothing
        - resizing
        - pasted regions
        - resampling
    """

    h, w = image.shape[:2]

    x1, y1, x2, y2 = _circle_bbox(
        x,
        y,
        r,
        w,
        h
    )

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return 0.0, []

    gray_roi = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Inner stamp mask
    # --------------------------------------------------------

    inner_mask = np.zeros(
        gray_roi.shape,
        dtype=np.uint8
    )

    cv2.circle(
        inner_mask,
        (
            int(x - x1),
            int(y - y1)
        ),
        max(
            2,
            int(r * 0.75)
        ),
        255,
        -1
    )

    # --------------------------------------------------------
    # Outer ring
    # --------------------------------------------------------

    outer_mask = np.zeros(
        gray_roi.shape,
        dtype=np.uint8
    )

    cv2.circle(
        outer_mask,
        (
            int(x - x1),
            int(y - y1)
        ),
        max(
            3,
            int(r * 1.15)
        ),
        255,
        -1
    )

    # Remove inner area from outer ring.
    outer_mask[
        inner_mask > 0
    ] = 0

    inner_pixels = gray_roi[
        inner_mask > 0
    ]

    outer_pixels = gray_roi[
        outer_mask > 0
    ]

    if (
        len(inner_pixels) < 50
        or len(outer_pixels) < 50
    ):
        return 0.0, []

    # --------------------------------------------------------
    # Laplacian texture
    # --------------------------------------------------------

    laplacian = cv2.Laplacian(
        gray_roi,
        cv2.CV_64F
    )

    inner_texture = np.std(
        laplacian[
            inner_mask > 0
        ]
    )

    outer_texture = np.std(
        laplacian[
            outer_mask > 0
        ]
    )

    if outer_texture <= 1e-6:
        return 0.0, []

    ratio = (
        inner_texture
        / outer_texture
    )

    reasons = []

    # A very smooth stamp compared with the surrounding
    # document is suspicious.
    if ratio < 0.35:

        reasons.append(
            "Stamp region is noticeably smoother than "
            "the surrounding document "
            f"(local texture ratio={ratio:.2f}x), "
            "which may indicate smoothing, resampling, "
            "or a pasted image."
        )

    # --------------------------------------------------------
    # Convert ratio into anomaly score
    # --------------------------------------------------------

    if ratio < 1.0:

        anomaly = _clamp(
            (0.90 - ratio) / 0.90
        )

    else:

        anomaly = _clamp(
            (ratio - 1.0) / 1.5
        )

    return anomaly, reasons


# ============================================================
# BOUNDARY ANALYSIS
# ============================================================

def _analyze_boundary(image, x, y, r):
    """
    Check whether the transition between the stamp and
    surrounding document is unusually abrupt.

    A pasted or edited region may have a visible rectangular
    or artificial boundary.
    """

    h, w = image.shape[:2]

    x1, y1, x2, y2 = _circle_bbox(
        x,
        y,
        int(r * 1.30),
        w,
        h
    )

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        return 0.0, []

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    cx = int(x - x1)
    cy = int(y - y1)

    # Sample narrow rings around the stamp.
    ring_values = []

    for radius in [
        int(r * 0.90),
        int(r * 1.00),
        int(r * 1.10),
        int(r * 1.20)
    ]:

        mask_outer = np.zeros(
            gray.shape,
            dtype=np.uint8
        )

        mask_inner = np.zeros(
            gray.shape,
            dtype=np.uint8
        )

        cv2.circle(
            mask_outer,
            (cx, cy),
            radius + 3,
            255,
            -1
        )

        cv2.circle(
            mask_inner,
            (cx, cy),
            max(1, radius - 3),
            255,
            -1
        )

        ring = cv2.subtract(
            mask_outer,
            mask_inner
        )

        values = gray[
            ring > 0
        ]

        if len(values) > 10:
            ring_values.append(
                float(np.mean(values))
            )

    if len(ring_values) < 2:
        return 0.0, []

    variation = float(
        np.std(ring_values)
    )

    reasons = []

    if variation > 25:

        reasons.append(
            "The stamp boundary shows unusually "
            "strong local intensity variation, "
            "which may indicate an artificial edit "
            "or pasted region."
        )

    anomaly = _clamp(
        (variation - 10.0) / 50.0
    )

    return anomaly, reasons


# ============================================================
# SINGLE STAMP ANALYSIS
# ============================================================

def _analyze_stamp(image, candidate):
    """
    Analyze one merged stamp region.
    """

    x, y, r = candidate["circle"]

    stamp_likelihood = candidate[
        "stamp_likelihood"
    ]

    # --------------------------------------------------------
    # Individual signals
    # --------------------------------------------------------

    color_score, color_reasons = (
        _analyze_color(
            image,
            x,
            y,
            r
        )
    )

    texture_score, texture_reasons = (
        _analyze_local_texture(
            image,
            x,
            y,
            r
        )
    )

    boundary_score, boundary_reasons = (
        _analyze_boundary(
            image,
            x,
            y,
            r
        )
    )

    seam_score, seam_reasons = _analyze_rectangular_seam(
        image,
        x,
        y,
        r
    )

    # --------------------------------------------------------
    # Final tamper score
    # --------------------------------------------------------

    # Hue variation alone is not considered a tamper signal because genuine
    # ink can contain anti-aliasing and color variation. It is retained as a
    # useful stamp-appearance signal.
    tamper_score = (
        boundary_score * BOUNDARY_WEIGHT
        + texture_score * TEXTURE_WEIGHT
        + seam_score * RECT_SEAM_WEIGHT
    )

    tamper_score = round(
        float(
            min(
                100.0,
                tamper_score
            )
        ),
        1
    )

    # --------------------------------------------------------
    # Verdict
    # --------------------------------------------------------

    if tamper_score >= SUSPICIOUS_THRESHOLD:

        verdict = "SUSPICIOUS"

    elif tamper_score >= REVIEW_THRESHOLD:

        verdict = "REVIEW_RECOMMENDED"

    else:

        verdict = "LIKELY_AUTHENTIC"

    # --------------------------------------------------------
    # Reasons
    # --------------------------------------------------------

    reasons = []

    reasons.extend(
        boundary_reasons
    )

    reasons.extend(
        texture_reasons
    )
    reasons.extend(
        seam_reasons
    )

    if not reasons:

        reasons.append(
            "No strong local indicators of stamp "
            "manipulation were detected."
        )

    return {
        "verdict": verdict,
        "tamper_score": tamper_score,
        "stamp_likelihood": stamp_likelihood,
        "bbox": _circle_bbox(
            x,
            y,
            r,
            image.shape[1],
            image.shape[0]
        ),
        "center": (
            int(x),
            int(y)
        ),
        "radius": int(r),
        "candidate_count": candidate.get(
            "candidate_count",
            1
        ),
        "reasons": reasons
    }



def _find_color_stamp_candidates(image):
    """Detect stamp-like ink clusters directly from color/saturation.

    The synthetic stamp uses colored ink while the clean document's
    circular clutter is grayscale. A small morphological close reconnects
    broken stamp strokes into one compact component.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]

    mask = np.where(saturation > 50, 255, 0).astype(np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    candidates = []

    h, w = image.shape[:2]
    for i in range(1, count):
        x, y, bw, bh, area = stats[i]

        if area < 500:
            continue
        if bw < 40 or bh < 40:
            continue
        if bw > min(w, 500) or bh > min(h, 500):
            continue

        aspect = bw / float(max(1, bh))
        if aspect < 0.55 or aspect > 1.8:
            continue

        # Stamp-like components should be reasonably compact, not long text.
        extent = area / float(max(1, bw * bh))
        if extent < 0.035:
            continue

        cx = int(x + bw / 2)
        cy = int(y + bh / 2)
        radius = int(max(bw, bh) / 2 + 2)

        likelihood = _stamp_likelihood(
            image,
            (cx, cy, radius)
        )

        # Color-component evidence is stronger than the noisy Hough score.
        likelihood = max(likelihood, 0.34)

        candidates.append({
            "circle": (cx, cy, radius),
            "stamp_likelihood": round(float(likelihood), 3),
            "candidate_count": 10,
            "color_component": True,
        })

    candidates.sort(
        key=lambda c: (
            c.get("color_component", False),
            c["stamp_likelihood"],
            c["circle"][2]
        ),
        reverse=True
    )
    return candidates


def _filter_stamp_candidates(image, candidates):
    """Reject ordinary circular clutter while retaining real ink stamps."""
    kept = []

    # If direct colored-ink detection found a stamp-sized component, prefer
    # those candidates and discard grayscale Hough clutter for this pass.
    color_candidates = [
        c for c in candidates
        if c.get("color_component", False)
    ]
    if color_candidates:
        candidates = color_candidates

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    for candidate in candidates:
        x, y, r = candidate["circle"]
        h, w = image.shape[:2]

        x1, y1, x2, y2 = _circle_bbox(x, y, r, w, h)
        roi_sat = saturation[y1:y2, x1:x2]
        roi_gray = gray[y1:y2, x1:x2]

        if roi_sat.size == 0:
            continue

        color_coverage = float(np.mean(roi_sat > 50))
        sat_mean = float(np.mean(roi_sat))
        structure_count = int(candidate.get("candidate_count", 1))

        # Strong colored ink is the preferred stamp cue.
        has_color = (
            color_coverage >= 0.025
            and sat_mean >= 8.0
        )

        # Fallback for monochrome seals: require several overlapping Hough
        # circles and a reasonably large physical region.
        has_structure = (
            structure_count >= 4
            and r >= 55
            and float(np.std(roi_gray)) >= 12.0
        )

        if has_color or has_structure:
            kept.append(candidate)

    return kept


def _analyze_rectangular_seam(image, x, y, r):
    """Detect a hard rectangular paste boundary around a stamp.

    The synthetic tampering test deliberately adds a one-pixel rectangle.
    A genuine circular seal should not create strong edges on all four
    sides of a square at approximately the same radius.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    cx, cy = int(x), int(y)
    radius = max(12, int(r))

    side_strengths = []
    side_lengths = []

    # Search a narrow band around the estimated square boundary. This allows
    # a few pixels of Hough/connected-component localization error.
    for delta in range(-3, 4):
        off = max(5, radius + delta)

        x_left = max(1, min(w - 2, cx - off))
        x_right = max(1, min(w - 2, cx + off))
        y_top = max(1, min(h - 2, cy - off))
        y_bottom = max(1, min(h - 2, cy + off))

        vert_left = np.abs(
            gray[max(0, cy - off):min(h, cy + off + 1), x_left + 1].astype(np.int16)
            - gray[max(0, cy - off):min(h, cy + off + 1), x_left - 1].astype(np.int16)
        )
        vert_right = np.abs(
            gray[max(0, cy - off):min(h, cy + off + 1), x_right + 1].astype(np.int16)
            - gray[max(0, cy - off):min(h, cy + off + 1), x_right - 1].astype(np.int16)
        )
        horiz_top = np.abs(
            gray[y_top + 1, max(0, cx - off):min(w, cx + off + 1)].astype(np.int16)
            - gray[y_top - 1, max(0, cx - off):min(w, cx + off + 1)].astype(np.int16)
        )
        horiz_bottom = np.abs(
            gray[y_bottom + 1, max(0, cx - off):min(w, cx + off + 1)].astype(np.int16)
            - gray[y_bottom - 1, max(0, cx - off):min(w, cx + off + 1)].astype(np.int16)
        )

        vals = [
            float(np.mean(vert_left)) if len(vert_left) else 0.0,
            float(np.mean(vert_right)) if len(vert_right) else 0.0,
            float(np.mean(horiz_top)) if len(horiz_top) else 0.0,
            float(np.mean(horiz_bottom)) if len(horiz_bottom) else 0.0,
        ]

        side_strengths.append(vals)
        side_lengths.append(float(np.mean(vals)))

    best_index = int(np.argmax(side_lengths))
    best = side_strengths[best_index]
    mean_strength = float(np.mean(best))
    strong_sides = sum(v >= 20.0 for v in best)

    # Need multiple strong sides, not just one text/graphic edge.
    if strong_sides >= 2 and mean_strength > 18.0:
        anomaly = _clamp((mean_strength - 15.0) / 30.0)
        reasons = [
            "A strong rectangular edge pattern was detected around the "
            f"stamp region (mean seam strength={mean_strength:.1f}), "
            "which is consistent with a hard-edged pasted or edited area."
        ]
        return anomaly, reasons

    return 0.0, []


def _expand_stamp_region(candidate, factor=1.30):
    """Expand a merged circle slightly so local seam/tamper evidence
    can see the edge of a pasted stamp region."""
    x, y, r = candidate["circle"]
    expanded = dict(candidate)
    expanded["circle"] = (x, y, max(r, int(r * factor)))
    return expanded


# ============================================================
# MAIN FUNCTION
# ============================================================

def detect_stamp_tampering(image_path: str):
    """
    Detect suspicious stamp/seal-like regions in a document.

    Returns a dictionary containing:
        - overall_verdict
        - stamp_count
        - regions
        - summary
    """

    # --------------------------------------------------------
    # Load image
    # --------------------------------------------------------

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    # --------------------------------------------------------
    # Detect circles
    # --------------------------------------------------------

    circles = _detect_circles(
        image
    )

    initial_circle_count = len(
        circles
    )

    # --------------------------------------------------------
    # Remove obvious duplicates
    # --------------------------------------------------------

    circles = _nms_circles(
        circles
    )

    # --------------------------------------------------------
    # Calculate stamp likelihood
    # --------------------------------------------------------

    candidates = []

    for circle in circles:

        likelihood = _stamp_likelihood(
            image,
            circle
        )

        if likelihood >= MIN_STAMP_LIKELIHOOD:

            candidates.append(
                {
                    "circle": circle,
                    "stamp_likelihood": likelihood
                }
            )

    # --------------------------------------------------------
    # No stamp
    # --------------------------------------------------------

    if not candidates:

        return {
            "overall_verdict": "NO_STAMP_DETECTED",
            "stamp_count": 0,
            "stamp_regions_detected": 0,
            "regions": [],
            "summary": (
                f"Found {initial_circle_count} circular "
                "shape(s), but none matched the visual "
                "characteristics of a stamp or seal."
            )
        }

    # --------------------------------------------------------
    # Merge candidates belonging to same stamp
    # --------------------------------------------------------

    merged_candidates = _merge_stamp_candidates(candidates)

    # --------------------------------------------------------
    # Direct colored-ink stamp detection
    # --------------------------------------------------------

    # Add a second detection source for colored stamp/seal ink. This is
    # particularly useful when Hough circles lock onto individual letters
    # or arcs instead of the whole stamp.
    color_hints = _find_color_stamp_candidates(image)
    if color_hints:
        merged_candidates.extend(color_hints)
        merged_candidates = _merge_stamp_candidates(merged_candidates)

    # --------------------------------------------------------
    # Second-stage visual filtering
    # --------------------------------------------------------

    merged_candidates = _filter_stamp_candidates(image, merged_candidates)

    if not merged_candidates:
        return {
            "overall_verdict": "NO_STAMP_DETECTED",
            "stamp_count": 0,
            "stamp_regions_detected": 0,
            "regions": [],
            "summary": (
                f"Found {initial_circle_count} circular shape(s), but "
                "none passed the stronger stamp/seal visual filter."
            )
        }

    # --------------------------------------------------------
    # Analyze merged stamp regions
    # --------------------------------------------------------

    regions = []

    for candidate in merged_candidates:

        result = _analyze_stamp(
            image,
            candidate
        )

        # Keep the original likelihood from the visual candidate.
        result["stamp_likelihood"] = candidate["stamp_likelihood"]
        regions.append(result)

    # --------------------------------------------------------
    # Overall verdict
    # --------------------------------------------------------

    suspicious_count = sum(
        1
        for region in regions
        if region["verdict"] == "SUSPICIOUS"
    )

    review_count = sum(
        1
        for region in regions
        if region["verdict"] == "REVIEW_RECOMMENDED"
    )

    if suspicious_count > 0:

        overall_verdict = "SUSPICIOUS"

    elif review_count > 0:

        overall_verdict = "REVIEW_RECOMMENDED"

    else:

        overall_verdict = "LIKELY_AUTHENTIC"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if overall_verdict == "LIKELY_AUTHENTIC":

        summary = (
            f"Detected {len(regions)} likely stamp/seal "
            f"region(s) from {initial_circle_count} "
            "circular candidate(s). All detected stamp "
            "regions appear consistent with an authentic "
            "stamp."
        )

    elif overall_verdict == "REVIEW_RECOMMENDED":

        summary = (
            f"Detected {len(regions)} likely stamp/seal "
            f"region(s) from {initial_circle_count} "
            "circular candidate(s). "
            f"{review_count + suspicious_count} "
            "region(s) require review or are suspicious."
        )

    else:

        summary = (
            f"Detected {len(regions)} likely stamp/seal "
            f"region(s) from {initial_circle_count} "
            "circular candidate(s). "
            f"{suspicious_count} region(s) show strong "
            "indicators of possible stamp manipulation."
        )

    return {
        "overall_verdict": overall_verdict,
        "stamp_count": len(regions),
        "stamp_regions_detected": len(regions),
        "regions": regions,
        "summary": summary
    }