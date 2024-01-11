import torch

import os
import sys
import json
import hashlib
import traceback
import math
import time
import random

from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
import numpy as np
import safetensors.torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))


import comfy.diffusers_load
import comfy.samplers
import comfy.sample
import comfy.sd
import comfy.utils
import comfy.controlnet

import comfy.clip_vision

import comfy.model_management
from comfy.cli_args import args

import importlib

import folder_paths
import latent_preview

from datetime import datetime

class EnhancedSaveNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "username": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": "USERNAME"
                }),
                "password": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": "PASSWORD"
                }),
                "url": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": "URL"
                }),
                "upload": ("BOOLEAN", {"default": True}),
                "verbose": ("BOOLEAN", {"default": True}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"})},
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
            }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def save_images(self, images, username, password, url, upload, verbose, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()

        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # file_name = f"{filename}_{counter:05}_.png"
            now = datetime.now()
            file_name = f"{filename}_{now.strftime('%Y-%m-%d-%H-%M-%S')}.png"
            full_path = os.path.join(full_output_folder, file_name)
            img.save(full_path, pnginfo=metadata, compress_level=self.compress_level)


            if upload:
                if verbose:
                    print(f"Uploading file {full_path}")

                from ftplib import FTP
                with FTP(url, username, password) as ftp, open(full_path, 'rb') as file_binary:
                    ftp.storbinary(f'STOR {file_name}', file_binary)
                    
                if verbose:
                    print("File upload success!")

            elif verbose:
                    print("Skipping file upload, disabled")

            results.append({
                "filename": file_name,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return { "ui": { "images": results } }

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "EnhancedSaveNode": EnhancedSaveNode
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "EnhancedSaveNode": "Enhanced Save Node"
}
