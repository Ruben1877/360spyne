# 🚗 Entraînement du Modèle de Segmentation

## Dataset Recommandé : Carvana (Kaggle)

Le dataset Carvana contient **5,088 images** de voitures avec masques parfaits.
C'est exactement ce dont Spyne a eu besoin pour entraîner leur modèle.

### Étapes :

1. **Télécharger le dataset**
   - Va sur https://www.kaggle.com/c/carvana-image-masking-challenge/data
   - Télécharge `train.zip` (images) et `train_masks.zip` (masques)
   - Place-les dans ce dossier

2. **Lancer l'entraînement**
   ```bash
   python train_segmentation.py --epochs 50 --batch-size 8
   ```

3. **Utiliser le modèle entraîné**
   ```bash
   python process_image.py photo.jpg output.jpg --model trained_model.pth
   ```

## Structure du Dataset

```
training/
├── data/
│   ├── train/           # Images de voitures
│   │   ├── 0001.jpg
│   │   └── ...
│   └── train_masks/     # Masques (noir/blanc)
│       ├── 0001_mask.png
│       └── ...
├── train_segmentation.py
└── trained_model.pth    # Modèle entraîné (après training)
```
