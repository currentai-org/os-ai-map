![AI Energy Score](/logo.png)

Welcome to AI Energy Score! This is an initiative to establish comparable energy efficiency ratings for AI models, helping the industry make informed decisions about sustainability in AI development.

## Key Links
- [Leaderboard](https://huggingface.co/spaces/AIEnergyScore/Leaderboard)
- [FAQ](https://huggingface.github.io/AIEnergyScore/#faq)
- [Documentation](https://huggingface.github.io/AIEnergyScore/#documentation)
- [Label Generator](https://huggingface.co/spaces/AIEnergyScore/Label)

## Quick Start

Get started benchmarking AI models in 5 steps:

### 1. Install Development Tools

```bash
cd AIEnergyScore

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies (for running scripts on host)
pip install -r requirements-dev.txt
```

### 2. Authenticate with HuggingFace (Optional - for gated models)

If you plan to test gated models (like Gemma or Llama):

```bash
# One-time login
hf auth login
```

### 3. Build the Docker Image

```bash
./build.sh
```

### 4. Run Your First Benchmark

```bash
# Quick test with default settings (10 samples)
./run_docker.sh --config-name text_generation backend.model=openai/gpt-oss-20b

# Or customize the number of samples
./run_docker.sh -n 100 --config-name text_generation backend.model=openai/gpt-oss-120b
```

### 5. View Results

Results are saved in `./results/` with energy data in:
- `GPU_ENERGY_WH.txt` - Total energy consumption
- `GPU_ENERGY_SUMMARY.json` - Detailed metrics

---

## Quick Start: Batch Testing

Test multiple models automatically from a CSV configuration:

```bash
cd AIEnergyScore

# Install development dependencies (if not already done)
source .venv/bin/activate
pip install -r requirements-dev.txt

# Test a single model first (recommended)
python batch_runner.py \
  --model-name "gpt-oss-20b" \
  --reasoning-state "High" \
  --num-prompts 3 \
  --output-dir ./test_run

# Run all gpt-oss Class A models (smaller models)
python batch_runner.py \
  --model-name gpt-oss \
  --num-prompts 10 \
  --class A
  --output-dir ./gpt_oss_results
```

Results are aggregated in `batch_results/master_results.csv` with detailed logs in `batch_results/logs/`. See [Batch Testing Multiple Models](#batch-testing-multiple-models) for full documentation.

**Next Steps:**
- [Compare different models](#example-comparing-energy-efficiency-across-models)
- [Run batch tests](#batch-testing-multiple-models)
- [Submit to the leaderboard](https://huggingface.co/spaces/AIEnergyScore/submission_portal)

---

## 🔐 Gated Model Support
AIEnergyScore supports **automatic authentication** for gated models on HuggingFace! Simply run `hf auth login` once (Step 2 above), and you'll have seamless access to models like Gemma, Llama, and other restricted models. See [Authentication for Gated Models](#authentication-for-gated-models) for details.


## Evaluating a Proprietary Model
### Hardware

The Dockerfile provided in this repository is made to be used on the NVIDIA H100-80GB GPU.
If you would like to run benchmarks on other types of hardware, we invite you to take a look at [these configuration examples](./text_generation.yaml) that can be run directly with [AI Energy Benchmark](https://github.com/neuralwatt/ai_energy_benchmarks/). However, evaluations completed on other hardware would not be currently compatable and comparable with the rest of the AI Energy Score data.


### Usage

#### Building the Docker Image

The Docker image includes both optimum-benchmark and ai_energy_benchmarks. Use the provided build script:

```bash
./build.sh
```

#### Quick Start with Helper Script

For convenience, use the provided helper script that handles all volume mounts automatically:

```bash
cd AIEnergyScore
./run_docker.sh --config-name text_generation backend.model=openai/gpt-oss-20b
```

The helper script automatically:
- Runs container as current user
- Mounts HuggingFace cache from `~/.cache/huggingface`
- **Automatically detects and mounts HuggingFace authentication tokens** (for gated models)
- Creates and mounts results directory
- Configures proper environment variables
- Defaults to 10 prompts (customize with `-n` or `--num-samples`)

> **Note for Gated Models**: If you need to access gated models (like `google/gemma-3-4b-pt` or Meta Llama models), run `huggingface-cli login` first. See [Authentication for Gated Models](#authentication-for-gated-models) for details.

**Examples:**
```bash
# Use default settings (10 samples)
./run_docker.sh --config-name text_generation backend.model=openai/gpt-oss-20b

# Test with 100 samples
./run_docker.sh -n 100 --config-name text_generation backend.model=openai/gpt-oss-120b

# Full test with 1000 samples
./run_docker.sh --num-samples 1000 --config-name text_generation backend.model=openai/gpt-oss-20b

# Use Optimum backend with HuggingFace optimum-benchmark
BENCHMARK_BACKEND=optimum ./run_docker.sh --config-name text_generation backend.model=openai/gpt-oss-20b
```

#### Authentication for Gated Models

Some models on HuggingFace (e.g., `google/gemma-3-1b-pt`, Meta Llama models) require authentication to access. The `run_docker.sh` script automatically handles authentication using two methods:

**Method 1: HuggingFace CLI Login (Recommended)**

The easiest way to authenticate is using the HuggingFace CLI:

```bash
# One-time setup: login to HuggingFace
huggingface-cli login #legacy
or
hf auth login 

# Then use normally - token is automatically mounted
./run_docker.sh --config-name text_generation backend.model=google/gemma-3-1b-pt
```

This creates a token file at `~/.huggingface/token` which is automatically detected and mounted by `run_docker.sh`.

**Method 2: HF_TOKEN Environment Variable**

Alternatively, you can pass your token explicitly:

```bash
# Get your token from https://huggingface.co/settings/tokens
export HF_TOKEN=hf_your_token_here

# Run with token from environment
HF_TOKEN=hf_xxx ./run_docker.sh --config-name text_generation backend.model=google/gemma-3-1b-pt
```
The `run_docker.sh` script will display a warning if no authentication is found when you run it.

#### Non-Docker Usage

For environments without Docker support or when you prefer direct execution, use the `run_non_docker.sh` script:

**Setup (first time only):**
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Authenticate with HuggingFace (for gated models)
huggingface-cli login
# or
hf auth login

# 4. Verify GPU access
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}')"
```

**Direct Mode - Run a single benchmark:**

Direct mode runs a single model using Hydra configuration syntax (`key=value`).

```bash
# Always activate virtual environment first
source .venv/bin/activate

# Basic usage with default settings (10 prompts, pytorch backend)
./run_non_docker.sh backend.model=openai/gpt-oss-20b

# Customize number of prompts
./run_non_docker.sh -n 100 backend.model=openai/gpt-oss-120b

# Override other Hydra config parameters
./run_non_docker.sh backend.model=openai/gpt-oss-20b scenario.dataset_name=custom.csv

# Using vLLM backend (requires running vLLM server)
./run_non_docker.sh -b vllm -e http://localhost:8021/v1 backend.model=openai/gpt-oss-20b
```

> **Note:** Direct mode accepts Hydra-style arguments (e.g., `backend.model=...`) and runs a single model.

**Batch Mode - Test multiple models from CSV:**

Batch mode runs multiple models from a CSV file using filter flags. **Important:** Hydra arguments like `backend.model=` don't work in batch mode - use `--model-name` instead.

```bash
# Activate virtual environment
source .venv/bin/activate

# Run specific model (use --model-name, NOT backend.model=)
./run_non_docker.sh --batch --model-name "openai/gpt-oss-20b" -n 10

# Run all Class A models
./run_non_docker.sh --batch --class A --output-dir ./class_a_results

# Filter by model name pattern (substring match)
./run_non_docker.sh --batch --model-name "Llama" -n 50

# Filter by reasoning state
./run_non_docker.sh --batch --reasoning-state "On (High)" --output-dir ./reasoning_tests

# Combine filters for precise selection
./run_non_docker.sh --batch --model-name "gpt-oss-20b" --reasoning-state "On (High)" -n 10

# Test all gpt-oss models (will match gpt-oss-20b and gpt-oss-120b)
./run_non_docker.sh --batch --model-name "gpt-oss" -n 10
```

> **Note:** Batch mode uses CSV-based filtering with `--model-name`, `--class`, `--reasoning-state`, etc. The `--model-name` flag uses substring matching, so `"gpt-oss"` matches all gpt-oss variants.

**Key Options:**

**Direct Mode (no `--batch` flag):**
- `-n, --num-samples NUM` - Number of prompts to test (default: 10, aliases: `--num-prompts`)
- `-b, --backend BACKEND` - Backend: pytorch, vllm, optimum (default: pytorch)
- `-e, --endpoint URL` - vLLM endpoint URL (default: http://localhost:8000/v1)
- `-h, --help` - Show help message
- Hydra config overrides: Pass as `key=value` arguments (e.g., `backend.model=...`, `scenario.dataset_name=...`)

**Batch Mode (requires `--batch` flag):**
- `--csv FILE` - Path to models CSV file (default: oct_2025_models.csv)
- `--output-dir DIR` - Output directory for results (default: ./batch_results)
- `--model-name PATTERN` - Filter by model name (substring match, e.g., "gpt-oss" matches all gpt-oss variants)
- `--class CLASS` - Filter by model class (A, B, or C)
- `--task TASK` - Filter by task type (e.g., text_gen, image_gen)
- `--reasoning-state STATE` - Filter by reasoning state (e.g., 'On', 'Off', 'On (High)')
- `-n, --num-prompts NUM` - Number of prompts per model (default: 10, alias: `--num-samples`)
- `--prompts-file FILE` - Path to custom prompts CSV file (optional)
- `-b, --backend BACKEND` - Backend selection (default: pytorch)
- `-e, --endpoint URL` - vLLM endpoint for vLLM backend

> **Important:** In batch mode, use filter flags (like `--model-name`) instead of Hydra arguments. Hydra-style arguments like `backend.model=...` are ignored in batch mode.

**Environment Variables:**
- `HF_TOKEN` - HuggingFace API token for gated models
- `HF_HOME` - HuggingFace cache location (default: ~/.cache/huggingface)
- `VENV_DIR` - Virtual environment directory (default: .venv)
- `RESULTS_DIR` - Results directory for Direct Mode (default: ./results)
- `PYTHON_BIN` - Python binary to use (default: auto-detected from .venv)

Results are saved in the specified output directory with the same structure as Docker mode.

#### Manual Usage

Alternatively, you can run your benchmark manually. **Important**: Create the results directory first to avoid permission errors:

```bash
# Create results directory with proper permissions
mkdir -p results

#for example
docker run --gpus all --shm-size 1g \
  --user $(id -u):$(id -g) \
  -v ~/.cache/huggingface:/home/user/.cache/huggingface \
  -v $(pwd)/results:/results \
  -e HOME=/home/user \
  ai_energy_score \
  --config-name text_generation \
  scenario.num_samples=3 \
  backend.model=openai/gpt-oss-20b

# For gated models, add token file mount and/or HF_TOKEN
docker run --gpus all --shm-size 1g \
  --user $(id -u):$(id -g) \
  -v ~/.cache/huggingface:/home/user/.cache/huggingface \
  -v ~/.huggingface/token:/home/user/.huggingface/token:ro \
  -v $(pwd)/results:/results \
  -e HOME=/home/user \
  -e HF_TOKEN=hf_your_token_here \
  ai_energy_score \
  --config-name text_generation \
  backend.model=google/gemma-3-1b-pt
```
where `my_task` is the name of a task with a configuration [here](https://github.com/huggingface/optimum-benchmark/tree/main/energy_star), `my_model` is the name of your model that you want to test (which needs to be compatible with either the Transformers or the Diffusers libraries) and `my_processor` is the name of the tokenizer/processor you want to use. In most cases, `backend.model` and `backend.processor` will be identical, except in cases where a model is using another model's tokenizer (e.g. from a LLaMa model).

The rest of the configuration is explained [here](https://github.com/huggingface/optimum-benchmark/)

### Backend Selection

AIEnergyScore supports multiple benchmark backends for flexibility and validation:

| Backend | Tool | Load Generation | Model Location | Use Case |
|---------|------|-----------------|----------------|----------|
| `pytorch` (default) | ai_energy_benchmarks | ai_energy_benchmarks generates load | Local GPU (in container) | Standard AIEnergyScore benchmarks |
| `optimum` | optimum-benchmark | optimum-benchmark generates load | Local GPU (in container) | Alternative HuggingFace backend |
| `vllm` | ai_energy_benchmarks | ai_energy_benchmarks generates load | External vLLM server | Production load testing |

**Default Backend (PyTorch):**

The default `pytorch` backend uses the [ai_energy_benchmarks](https://github.com/neuralwatt/ai_energy_benchmarks) framework, which loads models directly from HuggingFace or local paths for inference. This backend provides full control over model configuration including quantization, device mapping, and multi-GPU support. It measures raw model performance without serving overhead, making it ideal for controlled experiments and head-to-head model comparisons. The PyTorch backend automatically handles model sharding across multiple GPUs for large models and supports reasoning-capable models with automatic prompt formatting.

#### Default Usage (PyTorch/ai_energy_benchmarks)

```bash
# Standard AIEnergyScore benchmark - run as current user with cache mounting
docker run --gpus all --shm-size 1g \
  --user $(id -u):$(id -g) \
  -v ~/.cache/huggingface:/home/user/.cache/huggingface \
  -v $(pwd)/results:/results \
  -e HOME=/home/user \
  ai_energy_score \
  --config-name text_generation \
  scenario.num_samples=20 \
  backend.model=openai/gpt-oss-120b
```

**Volume mounts:**
- `~/.cache/huggingface:/home/user/.cache/huggingface` - Reuse local HuggingFace model cache (avoids re-downloading)
- `$(pwd)/results:/results` - Persist benchmark results to local directory
- `--user $(id -u):$(id -g)` - Run as current user (not root) for proper file permissions
- `-e HOME=/home/user` - Set HOME environment variable for HuggingFace cache location

#### Optimum Backend (optimum-benchmark)

```bash
# Use HuggingFace optimum-benchmark backend
docker run --gpus all --shm-size 1g \
  --user $(id -u):$(id -g) \
  -v ~/.cache/huggingface:/home/user/.cache/huggingface \
  -v $(pwd)/results:/results \
  -e HOME=/home/user \
  -e BENCHMARK_BACKEND=optimum \
  ai_energy_score \
  --config-name text_generation \
  backend.model=openai/gpt-oss-20b
```



**Note:** With `BENCHMARK_BACKEND=pytorch`, ai_energy_benchmarks loads the model and generates inference load directly on the GPU, just like optimum-benchmark.

## Example: Comparing Energy Efficiency Across Models

AIEnergyScore makes it easy to compare the energy efficiency of different models. Here are practical examples:

### Compare Small vs Large Models

```bash
cd AIEnergyScore

# Benchmark a smaller model (Class A: ~3B parameters)
./run_docker.sh -n 100 --config-name text_generation backend.model=HuggingFaceTB/SmolLM3-3B

# Benchmark a larger model (Class B: ~20B parameters)
./run_docker.sh -n 100 --config-name text_generation backend.model=openai/gpt-oss-20b
```

### Compare Different Model Families

```bash
# Benchmark Gemma family model
./run_docker.sh -n 100 --config-name text_generation backend.model=google/gemma-3-4b-pt

# Benchmark Qwen family model
./run_docker.sh -n 100 --config-name text_generation backend.model=Qwen/Qwen2.5-Coder-14B

# Benchmark Mistral family model
./run_docker.sh -n 100 --config-name text_generation backend.model=mistralai/Mistral-Nemo-Instruct-2407
```

### Compare Reasoning vs Non-Reasoning Modes

```bash
# Test with reasoning disabled (fixed 10 tokens)
./run_docker.sh -n 20 \
  --config-name text_generation \
  backend.model=openai/gpt-oss-20b \
  scenario.reasoning=False

# Test with low reasoning effort
./run_docker.sh -n 20 \
  --config-name text_generation \
  backend.model=openai/gpt-oss-20b \
  scenario.reasoning=True \
  scenario.reasoning_params.reasoning_effort=low

# Test with medium reasoning effort
./run_docker.sh -n 20 \
  --config-name text_generation \
  backend.model=openai/gpt-oss-20b \
  scenario.reasoning=True \
  scenario.reasoning_params.reasoning_effort=medium

# Test with high reasoning effort
./run_docker.sh -n 20 \
  --config-name text_generation \
  backend.model=openai/gpt-oss-20b \
  scenario.reasoning=True \
  scenario.reasoning_params.reasoning_effort=high
```

**Note:** Reasoning parameters are configured via Hydra command-line overrides. The system automatically detects the model type and applies the appropriate formatting (e.g., Harmony format for gpt-oss models). Legacy config files (`text_generation_gptoss_reasoning_*.yaml`) are deprecated but still functional for backward compatibility.

After running these benchmarks, results are saved in `./results/` with energy consumption data in `GPU_ENERGY_WH.txt` and `GPU_ENERGY_SUMMARY.json` files.

### Requirements Structure

AIEnergyScore uses two separate requirements files:

| File | Purpose | Usage |
|------|---------|-------|
| `requirements.txt` | Runtime dependencies for the Docker container | Installed automatically during `./build.sh` |
| `requirements-dev.txt` | Development/deployment tools for the host machine | Install with `pip install -r requirements-dev.txt` |

**Development requirements include:**
- `huggingface-hub[cli]` - Model downloads and authentication
- `pandas` - Batch runner CSV processing
- `pytest`, `ruff`, `mypy`, `black` - Testing and code quality tools
- `docker`, `python-dotenv`, `pyyaml` - Container and config management

### Running Tests

```bash
cd AIEnergyScore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Use `pytest -m e2e` to run only the end-to-end suites; omit the marker filter to execute the full test collection.

### Batch Testing Multiple Models

The `batch_runner.py` script enables automated testing of multiple models from a CSV configuration file, with support for model-specific parameters and reasoning configurations.

#### Quick Start (Docker Backend)

For the PyTorch backend (default), you only need development dependencies installed locally - all AI work runs in Docker:

```bash
cd AIEnergyScore

# Create virtual environment and install development dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Test a single model first (recommended)
python batch_runner.py \
  --model-name "gpt-oss-20b" \
  --reasoning-state "High" \
  --num-prompts 3 \
  --output-dir ./test_run

# Run batch tests (uses Docker internally)
python batch_runner.py \
  --model-name "gemma" \
  --output-dir ./results/gemma \
  --num-prompts 10
```

#### Common Usage Patterns

```bash
# Test all gpt-oss models
python batch_runner.py --model-name "gpt-oss" --num-prompts 20

# Test specific model class
python batch_runner.py --class A --num-prompts 50  # Small models
python batch_runner.py --class B --num-prompts 10  # Medium models
python batch_runner.py --class C --num-prompts 5   # Large models

# Filter by reasoning state
python batch_runner.py --reasoning-state "High" --num-prompts 10

# Combine filters
python batch_runner.py \
  --model-name gpt-oss \
  --reasoning-state "High" \
  --num-prompts 10

# Full benchmark run with timestamped output
python batch_runner.py \
  --output-dir ./full_results_$(date +%Y%m%d_%H%M%S)
```

#### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--csv` | Path to models CSV file | `AI Energy Score (Oct 2025) - Models.csv` |
| `--output-dir` | Output directory for results | `./batch_results` |
| `--backend` | Backend type: `pytorch`, `vllm` | `pytorch` |
| `--num-prompts` | Number of prompts to run | All prompts in dataset |
| `--prompts-file` | Custom prompts file | HuggingFace dataset |
| `--model-name` | Filter by model name (substring) | - |
| `--class` | Filter by model class (A/B/C) | - |
| `--reasoning-state` | Filter by reasoning state | - |
| `--task` | Filter by task type (text_gen, etc.) | - |

#### Output Structure

Results are organized with detailed logs and aggregated metrics:

```
batch_results/
├── master_results.csv          # Aggregated results from all runs
├── logs/                        # Debug logs for each model run
│   └── openai_gpt-oss-20b_On_High_*.log
└── individual_runs/             # Detailed per-model results
    └── openai_gpt-oss-20b_On_High/
        ├── benchmark_results.csv
        ├── GPU_ENERGY_WH.txt
        └── GPU_ENERGY_SUMMARY.json
```

**Key Metrics in master_results.csv:**
- `tokens_per_joule` - Energy efficiency (higher = better)
- `avg_energy_per_prompt_wh` - Energy cost per prompt (lower = better)
- `throughput_tokens_per_second` - Generation speed
- `gpu_energy_wh` - Total energy used
- `co2_emissions_g` - Carbon emissions

#### Checking Results

```bash
# View aggregated results
cat batch_results/master_results.csv

# View with formatted columns
column -t -s',' batch_results/master_results.csv | less -S

# Check success/failure counts
tail -n +2 batch_results/master_results.csv | \
  awk -F',' '{if ($19 == "") print "success"; else print "failed"}' | \
  sort | uniq -c

# View debug logs
cat batch_results/logs/*.log
```

#### Model-Specific Handling

The batch runner automatically configures model-specific parameters:

- **gpt-oss models**: Harmony formatting with reasoning effort levels
- **DeepSeek models**: `<think>` prefix for thinking mode
- **Qwen models**: `enable_thinking` parameter
- **Hunyuan models**: `/think` prefix
- **EXAONE models**: Inverted reasoning logic
- **Nemotron models**: `/no_think` for reasoning disable

#### Using vLLM Backend

For the vLLM backend (direct execution), you need the full `ai_energy_benchmarks` package:

```bash
# Install ai_energy_benchmarks from parent directory
pip install -e ../ai_energy_benchmarks[pytorch]
pip install -r requirements.txt

# Start vLLM server
vllm serve openai/gpt-oss-20b --port 8000

# Run with vLLM backend
python batch_runner.py \
  --backend vllm \
  --endpoint http://localhost:8000/v1 \
  --model-name "gpt-oss" \
  --num-prompts 10
```

#### Troubleshooting

**View available models:**
```bash
python model_config_parser.py "AI Energy Score (Oct 2025) - Models.csv"
```

**Test what models would run:**
```bash
python -c "
from model_config_parser import ModelConfigParser
parser = ModelConfigParser('AI Energy Score (Oct 2025) - Models.csv')
configs = parser.parse()
filtered = parser.filter_configs(configs, model_name='gpt-oss')
for c in filtered:
    print(f'{c.model_id} - {c.reasoning_state}')
"
```

**Missing dependencies:**
```bash
pip install pandas  # If pandas not installed
```

**Check logs for errors:**
```bash
# View most recent log
ls -t batch_results/logs/*.log | head -1 | xargs cat
```

#### vLLM Backend (ai_energy_benchmarks)

```bash
# Terminal 1: Start vLLM server
vllm serve openai/gpt-oss-120b --port 8000

# Terminal 2: Run benchmark (sends requests to external vLLM server)
docker run --gpus all --shm-size 1g \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/results \
  -e HOME=/home/user \
  -e BENCHMARK_BACKEND=vllm \
  -e VLLM_ENDPOINT=http://host.docker.internal:8000/v1 \
  ai_energy_score \
  --config-name text_generation \
  backend.model=openai/gpt-oss-120b
```

**Note:** vLLM backend requires a running vLLM server. The benchmark sends HTTP requests to measure energy under production-like serving conditions.

#### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BENCHMARK_BACKEND` | No | `pytorch` | Backend selection: `optimum`, `pytorch`, `vllm` |
| `VLLM_ENDPOINT` | Yes (for vLLM) | - | vLLM server endpoint (e.g., `http://localhost:8000/v1`) |

All backends produce compatible output files (`GPU_ENERGY_WH.txt`, `GPU_ENERGY_SUMMARY.json`) that can be submitted to the AIEnergyScore portal.

> [!WARNING]
> It is essential to adhere to the following GPU usage guidelines:
> - If the model being tested is classified as a Class A or Class B model (generally models with fewer than 66B parameters, depending on quantization and precision settings), testing must be conducted on a single GPU.
> - Running tests on multiple GPUs for these model types will invalidate the results, as it may introduce inconsistencies and misrepresent the model’s actual performance under standard conditions.

Once the benchmarking has been completed, the zipped log files should be uploaded to the [Submission Portal](https://huggingface.co/spaces/AIEnergyScore/submission_portal). The following terms and conditions will need to be accepted upon upload:

*By checking the box below and submitting your energy score data, you confirm and agree to the following:*

1. ***Public Data Sharing**: You consent to the public sharing of the energy performance data derived from your submission. No additional information related to this model including proprietary configurations will be disclosed.*
2. ***Data Integrity**: You validate that the log files submitted are accurate, unaltered, and generated directly from testing your model as per the specified benchmarking procedures.*
3. ***Model Representation**: You verify that the model tested and submitted is representative of the production-level version of the model, including its level of quantization and any other relevant characteristics impacting energy efficiency and performance.*

