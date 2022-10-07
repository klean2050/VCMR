"""Contains function to perform evaluation of supervised models on music tagging."""


import os
import torch
import torch.nn.functional as F
import numpy as np
from sklearn import metrics
import pickle
from tqdm import tqdm
from typing import Any


def evaluate(model: Any, test_dataset: Any, dataset_name: str, audio_length: int, output_dir: str, aggregation_method: str = "average", device: torch.device = None) -> None:
    """Performs evaluation of supervised models on music tagging.

    Args:
        model (pytorch_lightning.LightningModule): Supervised model to evaluate.
        test_dataset (torch.utils.data.Dataset): Test dataset.
        dataset_name (str): Name of dataset.
        audio_length (int): Length of raw audio input (in samples).
        output_dir (str): Path of directory for saving results.
        aggregation_method (str): Method to aggregate instance-level outputs of a song.
            Supported values: "average", "max", "majority_vote"
        device (torch.device): PyTorch device.
    
    Returns: None
    """

    # validate and set default values of parameters:
    if aggregation_method not in ["average", "max", "majority_vote"]:
        raise ValueError("Invalid aggregation method.")
    if device is None:
        device = torch.device("cuda")
    
    # lists of true labels, predicted labels, and features (embeddings):
    y_true = []
    y_pred = []
    features = []

    # run inference:
    model = model.to(device)
    model.eval()
    with torch.no_grad():
        for idx in tqdm(range(len(test_dataset))):
            # get label:
            _, label = test_dataset[idx]
            # get raw audio of song, split into non-overlapping segments of length audio_length:
            audio_song = test_dataset.concat_clip(idx, audio_length)
            audio_song = audio_song.squeeze(dim=1)
            assert audio_song.dim() == 3 and audio_song.size(dim=-1) == audio_length, "Error with shape of song audio."
            audio_song = audio_song.to(device)

            # pass song through model to get features (embeddings) and outputs (logits) of each segment:
            feat = model.encoder(audio_song)
            output = model.model(audio_song)
            # transform raw logits to probabilities:
            if dataset_name in ["magnatagatune", "mtg-jamendo-dataset"]:
                output = torch.sigmoid(output)
            else:
                output = F.softmax(output, dim=1)
            
            # average segment features across song = song-level feature:
            feat_song = feat.mean(dim=0)
            # aggregate segment output across song = song-level output (prediction):
            if aggregation_method == "average":
                pred_song = torch.mean(output, dim=0)
            elif aggregation_method == "max":
                pred_song = torch.amax(output, dim=0)
            elif aggregation_method == "majority_vote":
                pred_song = torch.mean(torch.round(output), dim=0)
            # sanity check shapes:
            assert feat_song.dim() == 1 and feat_song.size(dim=0) == feat.size(dim=-1), "Error with shape of song-level feature."
            assert pred_song.dim() == 1 and pred_song.size(dim=0) == output.size(dim=-1), "Error with shape of song-level output."
            
            # save true label, predicted label (song-level output), and song-level feature:
            y_true.append(label)
            y_pred.append(pred_song)
            features.append(feat_song)
    
    # convert lists to numpy arrays:
    y_true = torch.stack(y_true, dim=0).cpu().numpy()
    y_pred = torch.stack(y_pred, dim=0).cpu().numpy()
    features = torch.stack(features, dim=0).cpu().numpy()
    # sanity check shapes:
    assert y_true.ndim == 2, "Error with shape of true labels."
    assert y_pred.ndim == 2, "Error with shape of predicted labels."
    assert features.ndim == 2, "Error with shape of song-level features."
    assert y_true.shape == y_pred.shape, "Error with shape of true and/or predicted labels."

    # save true labels and song-level feature:
    np.save(os.path.join(output_dir, "labels.npy"), y_true)
    np.save(os.path.join(output_dir, "features.npy"), features)

    if dataset_name in ["magnatagatune", "mtg-jamendo-dataset"]:
        overall_dict = {
            "PR-AUC": metrics.average_precision_score(
                y_true, y_pred, average="macro"
            ),
            "ROC-AUC": metrics.roc_auc_score(y_true, y_pred, average="macro"),
        }
        with open(os.path.join(output_dir, "overall_dict.pickle"), "wb") as fp:
            pickle.dump(overall_dict, fp, protocol=pickle.HIGHEST_PROTOCOL)

        labels = test_dataset.dataset.label2idx.keys()
        labels = [name.split("---")[-1] for name in labels]

        prs = metrics.average_precision_score(y_true, y_pred, average=None)
        rcs = metrics.roc_auc_score(y_true, y_pred, average=None)
        classes_dict = {name: [v1, v2] for name, v1, v2 in zip(labels, prs, rcs)}
        with open(os.path.join(output_dir, "classes_dict.pickle"), "wb") as fp:
            pickle.dump(classes_dict, fp, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        y_pred = torch.stack(y_pred, dim=0)
        _, y_pred = torch.max(y_pred, 1)
        accuracy = metrics.accuracy_score(y_true, y_pred)
        print({"Accuracy": accuracy})

