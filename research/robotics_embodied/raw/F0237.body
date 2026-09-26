---
tags:
- robotics
---

<div align="center">
  <a href="https://github.com/NVIDIA/Isaac-GR00T">
    <img src="https://cdn-uploads.huggingface.co/production/uploads/67b8da81d01134f89899b4a7/8bFQa2ZIGCsOQQ2ho2N_U.png">
  </a>
  <div align="center">
  <a href="https://github.com/NVIDIA/Isaac-GR00T">
    <img src="https://img.shields.io/badge/GitHub-grey?logo=GitHub" alt="GitHub Badge">
  </a>
  <a href="https://developer.nvidia.com/isaac/gr00t">
    <img src="https://img.shields.io/badge/Website-green" alt="Website Badge">
  </a>
  <!-- <a href=""">
    <img src="https://img.shields.io/badge/Project%20Page-blue?style=plastic" alt="Project Page Badge">
  </a>
  <a href="">
    <img src="https://img.shields.io/badge/Research_Blog-black?style=flat" alt="Research Blog Badge">
  </a>
  <a href="">
    <img src="https://img.shields.io/badge/Dataset-Overview-brightgreen?logo=googleforms" alt="Research Blog Badge">
  </a>
  -->
</div>
</div>

# Model Overview

<p align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/67b8da81d01134f89899b4a7/ZCLLXZk2LQBG0YH_BmiIN.gif"
       style="width:100%; max-width:1000px; height:auto;">
</p>

## Description:
NVIDIA Isaac GR00T N1.7 is an open foundation model for generalized humanoid robot reasoning and skills. This cross-embodiment model takes multimodal input, including language and images, to perform manipulation tasks in diverse environments. Developers and researchers can post-train GR00T N1.7 with real or synthetic data for their specific humanoid robot or task.

Isaac GR00T N1.7 is the medium-sized version of our model built using pre-trained vision and language encoders, and uses a flow matching action transformer to model a chunk of actions conditioned on vision, language and proprioception. 

A detailed description of the Isaac GR00T N1.X architecture is provided in the GROOT N1 White Paper (https://arxiv.org/abs/2503.14734). 

This model is ready for commercial/non-commercial use.

**Model Developer**: NVIDIA

## Model Versions
The Isaac GR00T N1.7 model family includes the following 4 models:

### GR00T N1.7 – SimplerEnv Bridge

**Description**  
N1.7 post-trained model using the **Bridge Dataset** in SimplerEnv.

**Post-Training Data**  
https://huggingface.co/datasets/IPEC-COMMUNITY/bridge_orig_lerobot

**Dataset Summary**  
A LeRobot-format conversion of **BridgeData V2**, originally containing **60,096 trajectories** of robot manipulation across **24 environments**.

### GR00T N1.7 – SimplerEnv Fractal

**Description**  
N1.7 post-trained model using the **Fractal Dataset** in SimplerEnv.

**Post-Training Data**  
https://huggingface.co/datasets/IPEC-COMMUNITY/bridge_orig_lerobot

**Dataset Summary**  
A LeRobot-format conversion of **BridgeData V2**, originally containing **60,096 trajectories** of robot manipulation across **24 environments**.

### GR00T N1.7 – Droid
**Description**  
N1.7 post-trained model using the **DROID Dataset**.

**Post-Training Data**  
https://droid-dataset.github.io/

**Dataset Summary**  
A large-scale **“in-the-wild” robot manipulation dataset** with approximately **76,000 demonstration trajectories (~350 hours)** of interaction data, collected across **564 distinct scenes in 52 buildings**, covering **86 manipulation tasks** from natural-language instructions.

### GR00T N1.7 – LIBERO
**Description**  
N1.7 post-trained model using the **LIBERO Dataset**.

**Post-Training Data**  
https://github.com/Lifelong-Robot-Learning/LIBERO

**Dataset Summary**  
A benchmark for **lifelong robot learning**, providing **130 language-conditioned manipulation tasks** grouped into multiple task suites.  
Includes **human-teleoperated demonstrations** designed to evaluate **knowledge transfer and continual learning** in robotic agents.

## License
This model is released under the  [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).


### Deployment Geography:
Global

### Use Case:
Researchers, Academics, Open-Source Community: AI-driven robotics research and algorithm development.
Developers: Integrate and customize AI for various robotic applications.
Startups & Companies: Accelerate robotics development and reduce training costs.

### Release Date:
* Github via https://github.com/NVIDIA/Isaac-GR00T
* Huggingface via https://huggingface.co/collections/nvidia/gr00t-n17 

## Computational Load (Internal Only: For NVIDIA Models Only)
Cumulative Compute: Follow Instructions
 Estimated Energy and Emissions for Model Training: Follow Instructions
Total kWh:
64 GB200 nodes * 4 gpus per node x 1200W x 0.001 x 0.8 x 120 hours * 1.4 =  41288 kWh
Total Emission:
410.5 * 41288 * 0.000001 = 16.949 tCO2e

## Model Architecture:

**GR00T-N1.7 VLM backbone is now [Cosmos-Reason2-2B](https://huggingface.co/nvidia/Cosmos-Reason2-8B)**

**Network Architecture:** 

The schematic diagram is shown in the illustration above.
Red, Green, Blue (RGB) camera frames are processed through a pre-trained vision transformer (SigLip2).
Text is encoded by a pre-trained transformer (T5)
Robot proprioception is encoded using a multi-layer perceptron (MLP) indexed by the embodiment ID. To handle variable-dimension proprioception, inputs are padded to a configurable max length before feeding into the MLP.
Actions are encoded and velocity predictions decoded by an MLP, one per unique embodiment.
The flow matching transformer is implemented as a diffusion transformer (DiT), in which the diffusion step conditioning is implemented using adaptive layernorm (AdaLN).

![Model Architecture](model-architecture.png)

**Number of Model Parameters:** 3,000,000,000

## Input:
**Input Type(s):**
-Vision: Image Frames
-State: Robot Proprioception
-Language Instruction: Text
-Embodiment ID: Integer

**Input Format:**
-Vision: Variable number of uint8 image frames, coming from robot cameras
-State: Floating Point
-Language Instruction: String
-Embodiment ID: Integer indicating which of the training embodiments is observed

**Input Parameters:**
-Vision: Two-Dimensional (2D) - Red, Green, Blue (RGB)
-State: One-Dimensional (1D) - Floating number vector
-Language Instruction: One-Dimensional (1D) - String
-Embodiment ID: One-Dimensional (1D) - Integer

## Output:
**Output Type(s):** Actions

**Output Format** Continuous-value vectors

**Output Parameters:** [Two-Dimensional (2D)] <br>

**Other Properties Related to Output:** Continuous-value vectors correspond to different motor controls on a robot, which depends on Degrees of Freedom of the robot embodiment.

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA’s hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>

## Software Integration:

**Runtime Engine(s):** PyTorch

**Supported Hardware Microarchitecture Compatibility:** 
All of the below:
* NVIDIA Ampere
* NVIDIA Blackwell
* NVIDIA Jetson
* NVIDIA Hopper
* NVIDIA Lovelace

**[Preferred/Supported] Operating System(s):**
* Linux

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

# Model Version
GR00T N1.7 EA

# Training and Evaluation Datasets:
The total size (in number of data points): 21.6 million <br>
Total number of datasets: 13 <br>   


## Training Dataset:
GR00T Pretraining Data

**Data Collection Method by dataset:** Hybrid: Human, Robot, Simulated.

**Labeling Method by dataset:** Hybrid: Human, Automated.

**Properties:** 
* Cross-embodiment: Data collected on various robot embodiments 
* Sensor types: RGB camera, robot proprioception, robot actuator data


## Evaluation:
We evaluate in both simulation and real robot benchmarks, as defined in the White Paper (https://arxiv.org/abs/2503.14734). 

**Data Collection Method by dataset:** Hybrid: Human, Robot, Simulated.

**Labeling Method by dataset:** Hybrid: Human, Automated.

* Sim evaluation benchmarks for upper body control
* 9 DexMG Whitepaper tasks
* 24 RoboCasa simulated mobile manipulator tasks
* 24 Digital Cousin simulated GR-1 humanoid manipulation tasks 
* For sim, we automatically measure the success rate in each manipulation behavior.
* For real robot
    * Grocery packing task
    * Novel objects (unseen from training data)
    * Industrial multi-robot coordination with handoffs
    * Evaluated by human observers in the lab

## System Requirements and Performance

This section discusses the various configurations and inference runtimes for GR00T N1.7 tasks. We discuss both latency and speedup.

GR00T N1.7 Inference Timing (4 denoising steps, 1 camera):

| Device | Mode | Data Processing | Backbone | Action Head | E2E | Frequency | E2E Speedup |
|--------|------|-----------------|----------|-------------|-----|-----------|-------------|
| **dGPU** | | | | | | | |
| H100 80GB HBM3 | PyTorch Eager | 6.2 ms | 31.3 ms | 48.2 ms | 85.8 ms | 11.7 Hz | 1.00x |
| | torch.compile | 6.2 ms | 30.4 ms | 12.0 ms | 48.6 ms | 20.6 Hz | 1.77x |
| | **TensorRT (Full Pipeline)** | **6.2 ms** | **8.8 ms** | **12.3 ms** | **27.9 ms** | **35.9 Hz** | **3.08x** |
| H20 96GB HBM3 | PyTorch Eager | 5.33 ms | 30.8 ms | 47.3 ms | 83.4 ms | 12.0 Hz | 1.00x |
| | torch.compile | 5.33 ms | 31.1 ms | 13.3 ms | 49.7 ms | 20.1 Hz | 1.68x |
| | **TensorRT (Full Pipeline)** | **5.33 ms** | **14.2 ms** | **14.5 ms** | **34.0 ms** | **29.4 Hz** | **2.45x** |
| RTX Pro 6000 Blackwell | PyTorch Eager | 4.8 ms | 29.3 ms | 44.0 ms | 78.4 ms | 12.8 Hz | 1.00x |
| | torch.compile | 4.8 ms | 29.4 ms | 16.5 ms | 50.7 ms | 19.7 Hz | 1.55x |
| | **TensorRT (Full Pipeline)** | **4.8 ms** | **9.9 ms** | **13.2 ms** | **27.9 ms** | **35.9 Hz** | **2.81x** |
| RTX Pro 5000 72GB | PyTorch Eager | 8.85 ms | 54.01 ms | 63.19 ms | 126.4 ms | 7.9 Hz | 1.00x |
| | torch.compile | 8.85 ms | 55.74 ms | 20.38 ms | 84.9 ms | 11.8 Hz | 1.49x |
| | **TensorRT (Full Pipeline)** | **8.85 ms** | **14.37 ms** | **17.33 ms** | **40.5 ms** | **24.7 Hz** | **3.13x** |
| L40 | PyTorch Eager | 6.6 ms | 42.8 ms | 78.9 ms | 128.3 ms | 7.8 Hz | 1.00x |
| | torch.compile | 6.6 ms | 42.7 ms | 19.8 ms | 69.0 ms | 14.5 Hz | 1.86x |
| | **TensorRT (Full Pipeline)** | **6.6 ms** | **13.1 ms** | **18.8 ms** | **38.4 ms** | **26.0 Hz** | **3.34x** |
| L20 | PyTorch Eager | 5.7 ms | 47.58 ms | 86.92 ms | 140.3 ms | 7.1 Hz | 1.00x |
| | torch.compile | 5.7 ms | 47.2 ms | 20.18 ms | 73.1 ms | 13.7 Hz | 1.92x |
| | **TensorRT (Full Pipeline)** | **5.7 ms** | **17.27 ms** | **19.79 ms** | **42.8 ms** | **23.3 Hz** | **3.28x** |
| **Jetson / Spark** | | | | | | | |
| DGX Spark | PyTorch Eager | 13.14 ms | 38.22 ms | 74.94 ms | 126.4 ms | 7.9 Hz | 1.00x |
| | torch.compile | 13.14 ms | 39.23 ms | 56.49 ms | 108.8 ms | 9.2 Hz | 1.16x |
| | **TensorRT (Full Pipeline)** | **13.14 ms** | **33.43 ms** | **52.37 ms** | **98.6 ms** | **10.1 Hz** | **1.28x** |
| AGX Thor | PyTorch Eager | 8.21 ms | 55.26 ms | 81.65 ms | 144.9 ms | 6.9 Hz | 1.00x |
| | torch.compile | 8.21 ms | 55.59 ms | 64.66 ms | 128.4 ms | 7.8 Hz | 1.13x |
| | **TensorRT (Full Pipeline)** | **8.21 ms** | **28.89 ms** | **56.64 ms** | **93.8 ms** | **10.7 Hz** | **1.54x** |
| Orin | PyTorch Eager | 9.45 ms | 127.6 ms | 205.39 ms | 342.8 ms | 2.9 Hz | 1.00x |
| | torch.compile | 9.45 ms | 128.59 ms | 78.94 ms | 217.0 ms | 4.6 Hz | 1.58x |
| | **TensorRT (DiT-only)** | **9.45 ms** | **128.38 ms** | **78.6 ms** | **216.5 ms** | **4.6 Hz** | **1.58x** |

> **Note:** Orin uses DiT-only TensorRT (`--inference-mode tensorrt`) because TRT 10.3 does not support the backbone engine. All other platforms use the full pipeline (`--inference-mode trt_full_pipeline`).


## Inference:
**Engine:** PyTorch
**Test Hardware:** A6000

## Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.  

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

For more detailed information on ethical considerations for this model, please see the Model Card++ Explainability, Bias, Safety & Security, and Privacy Subcards.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).