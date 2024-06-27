import numpy as np


class SparseImage:
    def __init__(self, sparseFeatures, imageSize):
        self.sparseFeatures = sparseFeatures
        self.imageSize = imageSize


def compute_sample_size(imageShape, sparsityPercent):
    return int(imageShape[0]*imageShape[1] * sparsityPercent / 100)


def compute_image_of_relative_gradients(image):
    gradients_x = np.gradient(image, axis=1)
    gradients_y = np.gradient(image, axis=0)
    relativeGradientsImage = np.sqrt(gradients_x ** 2 + gradients_y ** 2)
    maxGradient = np.max(relativeGradientsImage)

    if maxGradient != 0.0:
        return relativeGradientsImage/maxGradient

    return relativeGradientsImage


def detect_sharp_edges_indices(relativeGradientsImage, sparsityPercent):
    sampleSize = compute_sample_size(relativeGradientsImage.shape, sparsityPercent)
    relativeGradientsFlat = np.ravel(relativeGradientsImage)

    threshold = np.partition(relativeGradientsFlat, -sampleSize)[-sampleSize]
    sharpEdgesIndices = np.where(relativeGradientsFlat >= threshold)[0][:sampleSize]
    return sharpEdgesIndices


def calculate_pixel_interests(relativeGradientsImage, sharpEdgeIndices):
    if any(x < 0 or x >= relativeGradientsImage.size for x in sharpEdgeIndices):
        raise ValueError("Index value out of range")
    return np.ravel(relativeGradientsImage)[sharpEdgeIndices]


def calculate_pixelwise_dtime(pixelInterests, availableDwellTimes):
    normalizedPixelInterests = (pixelInterests - np.min(pixelInterests))/(np.max(pixelInterests)-np.min(pixelInterests))
    maxDwellTime = max(availableDwellTimes)
    minDwellTime = min(availableDwellTimes)
    dwellTimes = minDwellTime + normalizedPixelInterests * (maxDwellTime - minDwellTime)
    return np.asarray([min(availableDwellTimes, key=lambda x: abs(x - dtime))for dtime in dwellTimes])


def extract_sparse_features(extractedImage, sparsityPercent, availableDwellTimes):
    relativeGradientsImage = compute_image_of_relative_gradients(extractedImage)
    sharpEdgesIndices = detect_sharp_edges_indices(relativeGradientsImage, sparsityPercent)
    pixelInterests = calculate_pixel_interests(relativeGradientsImage, sharpEdgesIndices)

    if max(pixelInterests) == 0:
        raise RuntimeError("Useless Image. No edges present")

    estDwellTime = calculate_pixelwise_dtime(pixelInterests, availableDwellTimes)

    return np.array([sharpEdgesIndices, pixelInterests, estDwellTime])


def generate_sparse_image(imageObject, sparsityPercent, availableDwellTimes):
    if sparsityPercent < 0 or sparsityPercent > 100:
        raise ValueError("illegal sparsity percentage")

    imageSizeDef = imageObject.imageSize
    ourImage = imageObject.extractedImage
    sparseFeatures = extract_sparse_features(ourImage, sparsityPercent, availableDwellTimes)

    return SparseImage(sparseFeatures, imageSizeDef)
