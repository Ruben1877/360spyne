#!/bin/bash
# 🚗 Setup Training Environment

echo "🚗 Setting up Car Segmentation Training"
echo "========================================"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install torch torchvision tqdm pillow --quiet

# Create data directory
mkdir -p data/train data/train_masks

echo ""
echo "✅ Setup complete!"
echo ""
echo "📥 Next steps:"
echo ""
echo "1. Download Carvana dataset from Kaggle:"
echo "   https://www.kaggle.com/c/carvana-image-masking-challenge/data"
echo ""
echo "2. Extract the files:"
echo "   - train.zip → data/train/"
echo "   - train_masks.zip → data/train_masks/"
echo ""
echo "3. Start training:"
echo "   python3 train_segmentation.py --epochs 50 --batch-size 8"
echo ""
echo "4. Use your trained model:"
echo "   python3 segment_with_trained.py car_segmentation_model.pth photo.jpg"

