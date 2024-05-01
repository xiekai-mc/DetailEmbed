import cv2
import numpy as np


def embed_image_to_large_image(
    big_image, small_image, small_edge_cut, corrosion, mask_center_and_scale
):
    small_image = small_image[
        small_edge_cut: small_image.shape[0] - small_edge_cut,
        small_edge_cut: small_image.shape[1] - small_edge_cut,
    ]

    # 初始化 SIFT 检测器
    sift = cv2.SIFT_create()

    mask = None
    if mask_center_and_scale is not None:
        if isinstance(mask_center_and_scale[0], int) or isinstance(
            mask_center_and_scale[0], float
        ):
            n = 1
            mask_center = mask_center_and_scale
        else:
            if len(mask_center_and_scale) > 2:
                print(
                    f"warning: the size of mask_center_and_scale {mask_center_and_scale} is not 2 or 1"
                )
            mask_center = mask_center_and_scale[0]
            n = mask_center_and_scale[1]

        y = big_image.shape[0] * mask_center[1]
        x = big_image.shape[1] * mask_center[0]
        h = small_image.shape[0]
        w = small_image.shape[1]
        # 创建与图像尺寸相同的空白掩码
        mask = np.zeros(big_image.shape[:2], dtype=np.uint8)
        # 在掩码中将矩形区域设置为白色（255）
        mask[
            max(int(y - (n * h) // 2), 0): min(
                int(y + (n * h) // 2), mask.shape[0] - 1
            ),
            max(int(x - (n * w) // 2), 0): min(
                int(x + (n * w) // 2), mask.shape[1] - 1
            ),
        ] = 255

    # 在大图和小图上检测关键点和描述符
    kp1, des1 = sift.detectAndCompute(big_image, mask)
    kp2, des2 = sift.detectAndCompute(small_image, None)

    # 使用 Flann 匹配器进行特征匹配
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict()
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # 筛选匹配的特征点
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # 获取匹配特征点的坐标
    src_pts = np.float32(
        [kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32(
        [kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 使用 RANSAC 算法估计仿射变换矩阵
    M, mask = cv2.estimateAffine2D(dst_pts, src_pts)
    # 将小图进行仿射变换
    h, w, _ = big_image.shape
    small_image_warped = cv2.warpAffine(small_image, M, (w, h))

    mask2 = cv2.threshold(small_image_warped, 0, 255, cv2.THRESH_BINARY)[1]
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (corrosion, corrosion))
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_ERODE, kernel)
    small_image_warped[mask2 == 0] = 0

    # 将变换后的小图覆盖到大图的对应位置
    result = big_image.copy()
    result[np.where(small_image_warped != 0)] = small_image_warped[
        np.where(small_image_warped != 0)
    ]
    return result


def embed_images_to_large_image(
    big_image_path,
    small_image_paths: list,
    small_edge_cut=0,
    corrosion=6,
    mask_center_and_scale_list: None | list = None,
):
    result = cv2.imread(big_image_path)
    for i, small_image_path in enumerate(small_image_paths):
        small_image = cv2.imread(small_image_path)
        mask_center_and_scale = None
        if mask_center_and_scale_list is not None:
            mask_center_and_scale = mask_center_and_scale_list[i]
        result = embed_image_to_large_image(
            result, small_image, small_edge_cut, corrosion, mask_center_and_scale
        )
        print(f"{i+1}/{len(small_image_paths)} has been embedded.")

    return result


if __name__ == "__main__":
    big_image_path = "images/Low-resolution.png"
    out_path = "images/out-keep-edge.png"
    small_image_paths = [
        "images/Deformed-high-resolution-partial.png",
        "images/High-resolution-partial2.png",
    ]
    out_image = embed_images_to_large_image(
        big_image_path, small_image_paths, small_edge_cut=0, corrosion=1
    )
    cv2.imwrite(out_path, out_image)

    out_path = "images/out.png"
    out_image = embed_images_to_large_image(
        big_image_path, small_image_paths, small_edge_cut=0, corrosion=3
    )
    cv2.imwrite(out_path, out_image)
