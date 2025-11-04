# VeinStitcher

A **Python-based application** for the **semi-automatic volumetric registration and stitching** of 3D confocal microscopy image stacks.

-----

## Description

VeinStitcher is designed to create a single, unified 3D volume from multiple, separately acquired confocal image stacks of the same object. This tool is essential for reconstructing large or complex biological structures that require tiling across multiple acquisitions.

The core functionality relies on a **user-guided, semi-automatic registration workflow**:

1.  **Landmark Definition:** The user manually identifies and marks **corresponding control points** on the overlapping regions of two input stacks.
2.  **Transformation Calculation:** The application uses these user-defined landmarks to compute the optimal **3D transformation matrix** (translation and rotation) required for precise alignment.
3.  **Volumetric Stitching:** The calculated transformation is applied to seamlessly merge the stacks into a single, combined 3D dataset.

-----

## Installation

### Dependencies

VeinStitcher requires a standard Python 3 environment along with several scientific computing libraries (e.g., NumPy, SciPy, image I/O). All required packages are specified in the `requirements.txt` file.

### Steps

1.  Clone the repository:
    ```bash
    git clone https://github.com/Fingal/VeinStitcher.git
    cd VeinStitcher
    ```
2.  Install dependencies using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

-----

## Usage

The application is run via the main Python script and guides the user through the alignment process.

1.  **Execute the Script:**
    ```bash
    python sticher.py
    ```
2.  **Load Inputs:** Load the two confocal stacks you intend to stitch.
3.  **Mark Points:** Interact with the application interface to precisely mark identical physical points across both volumes.
4.  **Stitch Output:** The program computes the transformation and outputs the final registered and merged 3D stack. For multi-stack projects, this process can be repeated sequentially to build a larger composite volume.

-----

## 📄 License

This project is open-source. Please refer to the repository's source files for licensing details.
