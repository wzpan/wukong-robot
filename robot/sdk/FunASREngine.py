
from typing import Any


class funASREngine(object):
    def __init__(self, inference_type, model_dir=''):
        assert inference_type in ['onnxruntime'] # 当前只实现了onnxruntime的推理方案
        self.inference_type = inference_type
        if self.inference_type == 'onnxruntime':
            # 调用下面的引擎进初始化引擎太慢了，因此放在条件分支里面
            from funasr_onnx import Paraformer
            self.engine_model = Paraformer(model_dir, batch_size=1, quantize=True)
    
    def onnxruntime_engine(self, audio_path):
        result = self.engine_model(audio_path)
        return str(result[0]['preds'][0])

    def __call__(self, fp):
        result = None
        if self.inference_type == 'onnxruntime':
            result = self.onnxruntime_engine(fp)
        return result