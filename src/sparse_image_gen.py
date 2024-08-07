import numpy as np
from skimage import filters


class SparseImageSEM:
    def __init__(self, sparseFeaturesSEM, imageSize):
        self.sparseFeaturesSEM = sparseFeaturesSEM
        self.imageSize = imageSize


class SparseImageSIMS:
    def __init__(self, sparseFeaturesSIMS, imageSize):
        self.sparseFeaturesSIMS = sparseFeaturesSIMS
        self.imageSize = imageSize


def compute_sample_size(imageShape, sparsityPercent):
    return int(imageShape[0] * imageShape[1] * sparsityPercent / 100)


def compute_image_of_relative_gradients(image):
    relativeGradientsImage = np.asarray(filters.sobel(image))
    maxGradient = np.max(relativeGradientsImage)

    if maxGradient != 0.0:
        return relativeGradientsImage / maxGradient

    return relativeGradientsImage


def detect_sharp_edge_locations(relativeGradientsImage, sparsityPercent):
    threshold = np.percentile(relativeGradientsImage, 100 - sparsityPercent)
    MaskOfSharpPixels = relativeGradientsImage >= threshold
    return np.where(MaskOfSharpPixels)


def calculate_pixel_interests(relativeGradientsImage, ySharpIndices, xSharpIndices):
    if any(y < 0 or y >= relativeGradientsImage.shape[0] for y in ySharpIndices):
        raise ValueError("Index value out of range")
    if any(x < 0 or x >= relativeGradientsImage.shape[1] for x in xSharpIndices):
        raise ValueError("Index value out of range")
    return relativeGradientsImage[ySharpIndices, xSharpIndices]


def calculate_pixelwise_dtime(pixelInterests, availableDwellTimes):
    normalizedPixelInterests = (pixelInterests - np.min(pixelInterests)) / (
            np.max(pixelInterests) - np.min(pixelInterests))
    maxDwellTime = max(availableDwellTimes)
    minDwellTime = min(availableDwellTimes)
    dwellTimes = minDwellTime + normalizedPixelInterests * (maxDwellTime - minDwellTime)
    return np.asarray([min(availableDwellTimes, key=lambda x: abs(x - dtime)) for dtime in dwellTimes])


def extract_sparse_features_sem(extractedImage, sparsityPercent, availableDwellTimes):
    relativeGradientsImage = compute_image_of_relative_gradients(extractedImage)
    ySharpIndices, xSharpIndices = detect_sharp_edge_locations(relativeGradientsImage, sparsityPercent)
    pixelInterests = calculate_pixel_interests(relativeGradientsImage, ySharpIndices, xSharpIndices)

    if max(pixelInterests) == 0:
        raise RuntimeError("Useless Image. No edges present")

    estDwellTime = calculate_pixelwise_dtime(pixelInterests, availableDwellTimes)

    return np.array([ySharpIndices, xSharpIndices, pixelInterests, estDwellTime])


def extract_sparse_features_sims(spectrometryImages, sparsityPercent, availableDwellTimes):
    ySharpIndices = []
    xSharpIndices = []
    pixelInterests = []
    estDwellTime = []

    for eachMassImage in spectrometryImages:
        y, x = detect_sharp_edge_locations(eachMassImage, sparsityPercent)
        ySharpIndices = np.array(np.append(ySharpIndices, y)).astype(int)
        xSharpIndices = np.array(np.append(xSharpIndices, x)).astype(int)
        pixelInterests = np.append(pixelInterests,
                                   calculate_pixel_interests(eachMassImage, ySharpIndices, xSharpIndices))
        estDwellTime = np.append(estDwellTime, calculate_pixelwise_dtime(pixelInterests, availableDwellTimes))

    if max(pixelInterests) == 0:
        raise RuntimeError("Useless Image")

    return np.array([ySharpIndices, xSharpIndices, pixelInterests, estDwellTime])


def generate_sparse_image_sem(imageObject, sparsityPercent, availableDwellTimes):
    if sparsityPercent < 0 or sparsityPercent > 100:
        raise ValueError("illegal sparsity percentage")

    imageSizeDef = imageObject.imageSize
    ourImage = imageObject.extractedImage
    sparseFeaturesSEM = extract_sparse_features_sem(ourImage, sparsityPercent, availableDwellTimes)

    return SparseImageSEM(sparseFeaturesSEM, imageSizeDef)


def generate_sparse_image_sims(imageObject, sparsityPercent, availableDwellTimes):
    if sparsityPercent < 0 or sparsityPercent > 100:
        raise ValueError("illegal sparsity percentage")

    imageSizeDef = imageObject.imageSize
    ourImage = imageObject.extractedImage
    sparseFeaturesSIMS = extract_sparse_features_sims(ourImage, sparsityPercent, availableDwellTimes)

    return SparseImageSEM(sparseFeaturesSIMS, imageSizeDef)
