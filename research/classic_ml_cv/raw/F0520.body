---
license: other
tags:
- vision
- image-segmentation
datasets:
- scene_parse_150
widget:
- src: https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg
  example_title: House
- src: https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000002.jpg
  example_title: Castle
---

# SegFormer (b0-sized) model fine-tuned on ADE20k

SegFormer model fine-tuned on ADE20k at resolution 512x512. It was introduced in the paper [SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers](https://arxiv.org/abs/2105.15203) by Xie et al. and first released in [this repository](https://github.com/NVlabs/SegFormer). 

Disclaimer: The team releasing SegFormer did not write a model card for this model so this model card has been written by the Hugging Face team.

## Model description

SegFormer consists of a hierarchical Transformer encoder and a lightweight all-MLP decode head to achieve great results on semantic segmentation benchmarks such as ADE20K and Cityscapes. The hierarchical Transformer is first pre-trained on ImageNet-1k, after which a decode head is added and fine-tuned altogether on a downstream dataset.

## Intended uses & limitations

You can use the raw model for semantic segmentation. See the [model hub](https://huggingface.co/models?other=segformer) to look for fine-tuned versions on a task that interests you.

### How to use

Here is how to use this model to classify an image of the COCO 2017 dataset into one of the 1,000 ImageNet classes:

```python
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
from PIL import Image
import requests

processor = SegformerImageProcessor.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits  # shape (batch_size, num_labels, height/4, width/4)
```

For more code examples, we refer to the [documentation](https://huggingface.co/transformers/model_doc/segformer.html#).

### License

The license for this model can be found [here](https://github.com/NVlabs/SegFormer/blob/master/LICENSE).

### BibTeX entry and citation info

```bibtex
@article{DBLP:journals/corr/abs-2105-15203,
  author    = {Enze Xie and
               Wenhai Wang and
               Zhiding Yu and
               Anima Anandkumar and
               Jose M. Alvarez and
               Ping Luo},
  title     = {SegFormer: Simple and Efficient Design for Semantic Segmentation with
               Transformers},
  journal   = {CoRR},
  volume    = {abs/2105.15203},
  year      = {2021},
  url       = {https://arxiv.org/abs/2105.15203},
  eprinttype = {arXiv},
  eprint    = {2105.15203},
  timestamp = {Wed, 02 Jun 2021 11:46:42 +0200},
  biburl    = {https://dblp.org/rec/journals/corr/abs-2105-15203.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
```
