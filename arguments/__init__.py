#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from argparse import ArgumentParser, Namespace
import sys
import os

class GroupParams:
    pass

class ParamGroup:
    def __init__(self, parser: ArgumentParser, name : str, fill_none = False):
        group = parser.add_argument_group(name)
        for key, value in vars(self).items():
            shorthand = False
            if key.startswith("_"):
                shorthand = True
                key = key[1:]
            t = type(value)
            value = value if not fill_none else None 
            if shorthand:
                if t == bool:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, action="store_true")
                else:
                    group.add_argument("--" + key, ("-" + key[0:1]), default=value, type=t)
            else:
                if t == bool:
                    group.add_argument("--" + key, default=value, action="store_true")
                else:
                    group.add_argument("--" + key, default=value, type=t)

    def extract(self, args):
        group = GroupParams()
        for arg in vars(args).items():
            if arg[0] in vars(self) or ("_" + arg[0]) in vars(self):
                setattr(group, arg[0], arg[1])
        return group

class ModelParams(ParamGroup): 
    def __init__(self, parser, sentinel=False):
        self.sh_degree = 2
        self._source_path = ""
        self._model_path = ""
        self._resolution = -1
        self._white_background = False
        self._load_iteration = -1
        self.data_device = "cuda"
        self.eval = False
        self.llffhold = 10
        self.num_images = -1
        self.scale_and_shift_mode = "mask"
        super().__init__(parser, "Loading Parameters", sentinel)

    def extract(self, args):
        g = super().extract(args)
        g.source_path = os.path.abspath(g.source_path)
        return g

class PipelineParams(ParamGroup):
    def __init__(self, parser):
        self.convert_SHs_python = False
        self.compute_cov3D_python = False
        self.debug = False
        super().__init__(parser, "Pipeline Parameters")

class OptimizationParams(ParamGroup):
    def __init__(self, parser):
        self.iterations = 9_000
        self.rotation_finetune_lr = 1e-2
        self.translation_finetune_lr = 1e-1
        self.scale_finetune_lr = 1e-1
        self.shift_finetune_lr = 1e-2
        
        self.rotation_lr_init   = 1e-4
        self.rotation_lr_final  = 1e-6
        self.translation_lr_init = 1e-3
        self.translation_lr_final = 1e-5
        self.camera_lr_max_steps = 9_000

        self.position_lr_init   = 0.0016
        self.position_lr_final  = 0.000016
        self.position_lr_delay_mult = 0.01
        self.position_lr_max_steps = 9_000
        self.feature_lr = 0.0025
        self.opacity_lr = 0.05
        self.scaling_lr = 0.005
        self.rotation_lr = 0.001
        self.percent_dense = 0.01
        self.lambda_dssim = 0.2
        self.densification_interval = 100
        self.opacity_reset_interval = 3000
        self.densify_from_iter = 500
        self.densify_until_iter = 9_000
        self.densify_grad_threshold = 0.0002
        self.cam_optim_from_iter = 0
        self.cam_optim_until_iter = 9_000

        # Progressive Elements
        self.register_steps = 200
        self.align_steps = 400
        self.loss_depth_correspondence_weight = 1e0
        self.loss_2d_correspondence_weight = 1e3
        self.loss_rgb_correspondence_weight = 1e1

        self.init_opacity = 0.999
        self.init_scale = 'distance'
        self.add_scale_factor = 1
        self.break_connection = True
        self.depth_diff_tolerance = 10
        self.correspondence_threshold = 0.5
        self.farest_percent = 1.
        self.retain_percent = 0.1
        self.dilate_kernel_size = 3
        self.add_frame_interval = 1
        
        super().__init__(parser, "Optimization Parameters")

def get_combined_args(parser : ArgumentParser):
    cmdlne_string = sys.argv[1:]
    cfgfile_string = "Namespace()"
    args_cmdline = parser.parse_args(cmdlne_string)

    try:
        cfgfilepath = os.path.join(args_cmdline.model_path, "cfg_args")
        print("Looking for config file in", cfgfilepath)
        with open(cfgfilepath) as cfg_file:
            print("Config file found: {}".format(cfgfilepath))
            cfgfile_string = cfg_file.read()
    except TypeError:
        print("Config file not found at")
        pass
    args_cfgfile = eval(cfgfile_string)

    merged_dict = vars(args_cfgfile).copy()
    for k,v in vars(args_cmdline).items():
        if v != None:
            merged_dict[k] = v
    return Namespace(**merged_dict)
