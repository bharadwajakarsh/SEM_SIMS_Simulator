import numpy as np
import matplotlib.pyplot as plt

from sparse_image_gen import extract_sparse_features_sem
from sparse_image_gen import SparseImageSEM, SparseImageSIMS
from initialize_database import SEMImage, SIMSImage
from stitch_images import stitch_images


def group_features_by_dwell_times(sparseFeatures):
    columnIndex = 2
    uniqueDwellTimes = np.unique(sparseFeatures[columnIndex])
    groupedSparseFeatures = {value: [] for value in uniqueDwellTimes}

    for eachDwellTime in uniqueDwellTimes:
        mask = sparseFeatures[columnIndex] == eachDwellTime
        featuresOfGroup = sparseFeatures[:, mask]
        groupedSparseFeatures[eachDwellTime] = featuresOfGroup

    return groupedSparseFeatures


def generate_scan_pattern(lowDTimageObject, sparsityPercent, availableDwellTimes, scanType):
    if not isinstance(lowDTimageObject, SEMImage):
        raise TypeError("First image should be of SEM Object type")
    if sparsityPercent < 0 or sparsityPercent > 100:
        raise ValueError("illegal sparsity percentage")
    if min(availableDwellTimes) < 0:
        raise ValueError("illegal dwell-time")

    ourImage = lowDTimageObject.extractedImage
    sparseFeatures = extract_sparse_features_sem(ourImage, sparsityPercent, availableDwellTimes)

    if scanType == "ascending":
        yImpPixelCoords = sparseFeatures[0, :].astype(int)
        xImpPixelCoords = sparseFeatures[1, :].astype(int)
        sortedIntensities = np.argsort(sparseFeatures[2, :])
        ycoords = yImpPixelCoords[sortedIntensities]
        xcoords = xImpPixelCoords[sortedIntensities]
        return ycoords, xcoords

    elif scanType == "descending":
        yImpPixelCoords = sparseFeatures[0, :].astype(int)
        xImpPixelCoords = sparseFeatures[1, :].astype(int)
        sortedIntensities = np.argsort(sparseFeatures[2, :])
        ycoords = yImpPixelCoords[sortedIntensities]
        xcoords = xImpPixelCoords[sortedIntensities]
        return ycoords[::-1], xcoords[::-1]

    elif scanType == "ascending plus raster":
        groupedSparseFeatures = group_features_by_dwell_times(sparseFeatures)
        groupedPixelLocations = {}
        for eachUniqueDwellTime in groupedSparseFeatures:
            xImportantPixels = np.array(groupedSparseFeatures[eachUniqueDwellTime][0, :]).astype(int)
            yImportantPixels = np.array(groupedSparseFeatures[eachUniqueDwellTime][1, :]).astype(int)
            combinedIndices = np.array(list(zip(yImportantPixels, xImportantPixels)))
            sortedPixelCoords = combinedIndices[np.lexsort((combinedIndices[:, 1], combinedIndices[:, 0]))]
            groupedPixelLocations[eachUniqueDwellTime] = sortedPixelCoords

        return groupedPixelLocations

    else:
        raise ValueError("Invalid scan type")


def display_scan_pattern(lowDTimageObject, sparsityPercent, availableDwellTimes, scanType):
    if scanType == "ascending" or scanType == "descending":
        ycoords, xcoords = generate_scan_pattern(lowDTimageObject, sparsityPercent, availableDwellTimes, scanType)
        plt.figure(figsize=(20, 20))
        plt.title("Path for scanning first 1000 pixels")
        plt.imshow(lowDTimageObject.extractedImage, cmap='grey')
        plt.plot(xcoords[:1000], ycoords[:1000], color='white', linewidth=1)
        plt.show()

    elif scanType == "ascending plus raster":
        groupedPixelLocations = generate_scan_pattern(lowDTimageObject, sparsityPercent, availableDwellTimes, scanType)
        for i, eachUniqueDwellTime in enumerate(groupedPixelLocations):
            ycoords = groupedPixelLocations[eachUniqueDwellTime][:, 0]
            xcoords = groupedPixelLocations[eachUniqueDwellTime][:, 1]
            plt.figure(figsize=(20, 20))
            plt.title(f"Path for scan number {i}. Dwell-time: {eachUniqueDwellTime}us")
            plt.imshow(lowDTimageObject.extractedImage, cmap='grey')
            plt.plot(xcoords[:1000], ycoords[:1000], color='white', linewidth=1)
            plt.show()
    else:
        raise ValueError("Invalid scan type")


def plot_dwell_times_histogram(dwellTimesFeature, bins: int):
    if len(dwellTimesFeature) == 0:
        raise ValueError("Empty dwell-times feature vector")
    if not isinstance(bins, int):
        bins = int(bins)

    plt.figure()
    plt.hist(dwellTimesFeature, bins)
    plt.xlabel("dwell time(us)")
    plt.ylabel("# pixels")
    plt.show()


def display_mask(sparseImageObject, originalImageObject):
    if not isinstance(sparseImageObject, (SparseImageSEM, SparseImageSIMS)):
        raise TypeError("Input should be a 'Sparse Image' object type, either SEM or SIMS")
    if not isinstance(originalImageObject, (SEMImage, SIMSImage)):
        raise TypeError("Input should be either SEM or SIMS image object type")

    imageToSee = np.zeros((sparseImageObject.imageSize, sparseImageObject.imageSize))
    yMaskCoords = sparseImageObject.sparseFeatures[0, :].astype(int)
    xMaskCoords = sparseImageObject.sparseFeatures[1, :].astype(int)
    imageToSee[yMaskCoords, xMaskCoords] = sparseImageObject.sparseFeatures[2, :]

    plt.figure()
    plt.title('Original image')
    plt.imshow(originalImageObject.extractedImage, cmap='grey')
    plt.show()
    plt.figure()
    plt.title('Mask of HIA')
    plt.imshow(imageToSee, cmap='binary')
    plt.show()


def display_stitched_image(lowDTImageObject, highDTImageObject, sparsityPercent):
    plt.figure()
    plt.imshow(lowDTImageObject.extractedImage, cmap='grey')
    plt.title("Low DT Image")
    plt.show()

    plt.figure()
    plt.imshow(highDTImageObject.extractedImage, cmap='grey')
    plt.title("High DT Image")
    plt.show()

    stitchedImageNormal = stitch_images(lowDTImageObject, highDTImageObject, sparsityPercent)
    plt.figure()
    plt.title("Normal stitching, dwell-times: {}".format([lowDTImageObject.dwellTime, highDTImageObject.dwellTime]))
    plt.imshow(stitchedImageNormal, cmap='grey')
    plt.show()


def calculate_psnr(originalImage, hybridImage):
    if np.linalg.norm(originalImage - hybridImage) == 0:
        return float('inf')
    return -20 * np.log10(np.mean((originalImage / np.max(originalImage) - hybridImage / np.max(hybridImage)) ** 2))


"""
Execution
from initialize_database import read_sem_images
from generate_new_images import generate_new_images
from sparse_image_gen import generate_sparse_image

path = "D:/Akarsh/Adaptive Scanning/Data/SEM_images_29_May_2024"
availableImages = read_sem_images(path)
imageSubset = availableImages[9:15]
newImageSet = generate_new_images(imageSubset, 4, 10)
imageSubset = sorted(imageSubset + newImageSet, key=lambda eachImage: eachImage.dwellTime)
firstTestImage = imageSubset[0]
secondTestImage = imageSubset[-1]
sparseImageObject = generate_sparse_image(firstTestImage, 15, np.array([10, 30, 40, 50, 100, 200, 300]))
display_mask(sparseImageObject, firstTestImage)
display_scan_pattern(firstTestImage, 15, np.array([50, 100, 200, 300]), "descending")
display_stitched_image(firstTestImage, secondTestImage, 15)
plot_dwell_times_histogram(sparseImageObject.sparseFeatures[2, :], 100)
print(compare_stitching_methods(firstTestImage, secondTestImage, 15, 3))
print(calculate_psnr(firstTestImage.extractedImage, stitch_images(firstTestImage, secondTestImage, 15)))
"""
