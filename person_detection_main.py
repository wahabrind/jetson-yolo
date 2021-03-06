import cv2
import numpy as np
import torch
# from torch._C import half

from models.experimental import attempt_load
from utils.general import check_img_size, non_max_suppression, set_logging
from utils.torch_utils import select_device


@torch.no_grad()
class Model():
    def __init__(self , model , confidence , iou):
        set_logging()
        self.confidence = confidence
        self.iou  = iou
        self.device = select_device('')
        self.half = False
        self.half &= self.device.type != 'cpu'  # half precision only supported on CUDA
        if model.lower() == 'm':
            self.model = attempt_load("personm2.pt", map_location=self.device)
        elif model.lower() == 'l':
            self.model = attempt_load("personl2.pt", map_location=self.device)
        else:
            raise Exception()
        if self.half:
            self.model.half()
        stride = int(self.model.stride.max())  # model stride
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names  # get class names
        imgsz = check_img_size(416, s=stride)  # check image size

    def run(self, image):
        self.image = image
        all = []

        height , width , _ = self.image.shape

        orgimg = image.copy()
        image = cv2.resize(self.image, (416, 416))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = np.moveaxis(image, -1, 0)
        image = torch.from_numpy(image).to(self.device)
        image = image.float() / 255.0  # 0 - 255 to 0.0 - 1.0
        if image.ndimension() == 3:
            image = image.unsqueeze(0)

        pred = self.model(image, augment=False)[0]

        pred = non_max_suppression(pred, self.confidence, self.iou, None, False, max_det=20)

        for i, det in enumerate(pred):  # per image
            if len(det):
                for *xyxy, conf, cls in reversed(det):
                    label = f'{self.names[int(cls)]} {conf:.2f}'

                    x1 = int(xyxy[0].item())
                    y1 = int(xyxy[1].item())
                    x2 = int(xyxy[2].item())
                    y2 = int(xyxy[3].item())


                    # normalizing bounding boxes

                    x1 = int((width*x1)/416)
                    y1 = int((height*y1)/416)
                    x2 = int((width*x2)/416)
                    y2 = int((height*y2)/416)

                    w = x2 - x1
                    h = y2 - y1

                    all.append([x1, y1, w, h])
                    cv2.rectangle(orgimg, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(orgimg, label, (x1, y1 - 20), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 0))

        return all, orgimg
