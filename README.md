# 🚗 Clone Spyne - 360° Car Photography Platform

> Open-source alternative to Spyne, built by reverse-engineering their APK. Professional automotive photography with AI-powered background removal and 360° spin views.

![Clone Spyne Demo](https://via.placeholder.com/800x400?text=Clone+Spyne+Demo)

## ✨ Features

- **📱 Guided Capture**: Overlay silhouettes guide perfect angle capture
- **🤖 AI Background Removal**: MediaPipe-powered segmentation
- **🎨 Studio Backgrounds**: Professional gradient backgrounds with floor/wall
- **🌑 Realistic Shadows**: 3-layer shadow system (contact, ambient, drop)
- **✨ Floor Reflections**: Mirror effect for premium look
- **🔄 360° Viewer**: Interactive spin views for web embedding
- **☁️ S3 Integration**: Scalable cloud storage
- **⚡ Job Queue**: Background processing with Bull/Redis

## 🏗️ Architecture

```
clone-spyne/
├── apps/
│   ├── mobile/          # React Native/Expo app
│   ├── web/             # Next.js dashboard
│   └── api/             # Express.js + Python ML
├── packages/
│   └── shared/          # Shared types & constants
└── assets/              # Silhouettes & overlays
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- Redis (for job queue)
- AWS account (for S3 storage)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/clone-spyne.git
cd clone-spyne

# Install Node.js dependencies
npm install

# Install Python dependencies
cd apps/api/python
pip install -r requirements.txt
cd ../../..

# Copy environment file
cp .env.example .env
# Edit .env with your AWS credentials

# Start development
npm run dev
```

### Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📖 Usage

### 1. Create a Vehicle

```bash
curl -X POST http://localhost:3001/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -d '{
    "make": "BMW",
    "model": "M4 Competition",
    "year": 2024,
    "type": "coupe"
  }'
```

### 2. Upload Images

Use the mobile app or web interface to capture and upload 8 photos.

### 3. Process Images

```bash
curl -X POST http://localhost:3001/api/v1/process/batch \
  -H "Content-Type: application/json" \
  -d '{
    "vehicleId": "your-vehicle-id",
    "options": {
      "backgroundPreset": "studio_white",
      "addReflection": true,
      "addShadows": true
    }
  }'
```

### 4. View 360° Result

Open `http://localhost:3000/vehicles/{id}` to see the interactive 360° viewer.

## 🔧 Processing Pipeline

The processing pipeline replicates Spyne's workflow exactly:

1. **Segmentation** - AI removes background (MediaPipe)
2. **Edge Smoothing** - Clean cutout edges (OpenCV)
3. **Background** - Generate studio gradient
4. **Shadows** - 3-layer shadow system
5. **Reflection** - Floor mirror effect
6. **Composite** - Layer assembly
7. **Post-process** - Final enhancements

### Python Usage

```python
from process_image import SpyneCloneProcessor

processor = SpyneCloneProcessor()
result = processor.process(
    input_path='car.jpg',
    output_path='car_processed.jpg',
    background_preset='studio_white',
    add_reflection=True
)
```

## 📱 Mobile App

The React Native app provides guided capture:

- Overlay silhouettes for each angle
- Progress tracking
- Direct upload to S3
- Offline support

```bash
cd apps/mobile
npm start
```

## 🌐 Web Dashboard

Next.js dashboard features:

- Vehicle inventory management
- Interactive 360° viewer
- Processing status tracking
- QR code for mobile capture

```bash
cd apps/web
npm run dev
```

## 🔍 Forensic Analysis

This project is based on forensic analysis of Spyne's Android APK:

| Element | Count |
|---------|-------|
| API Endpoints | 114 |
| Processing Parameters | 7,024 |
| Libraries | 15 |
| Classes | 2,220 |
| Constants | 6,239 |

Key discoveries:
- TensorFlow Lite + MediaPipe for segmentation
- MNN (Alibaba) as fallback
- RenderScript for GPU processing
- AWS S3 for asset storage

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## ⚠️ Disclaimer

This project is for educational purposes only. Spyne's assets, code, and branding are their intellectual property. This is a clean-room implementation using open-source alternatives.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

---

Built with ❤️ as an open-source alternative to Spyne

