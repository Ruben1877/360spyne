'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Car, 
  Camera, 
  Sparkles, 
  RotateCcw, 
  ArrowRight, 
  Play,
  CheckCircle2,
  Zap,
  Shield,
  Globe
} from 'lucide-react';

export default function HomePage() {
  const [isHovered, setIsHovered] = useState(false);

  const features = [
    {
      icon: Camera,
      title: 'Guided Capture',
      description: 'Overlay silhouettes guide perfect angle capture every time'
    },
    {
      icon: Sparkles,
      title: 'AI Background Removal',
      description: 'Instant professional studio backgrounds with ML-powered segmentation'
    },
    {
      icon: RotateCcw,
      title: '360° Spin Views',
      description: 'Interactive viewers that showcase vehicles from every angle'
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Process entire vehicle shoots in minutes, not hours'
    }
  ];

  const stats = [
    { value: '8-36', label: 'Capture Angles' },
    { value: '< 30s', label: 'Per Image' },
    { value: '4K', label: 'Output Quality' },
    { value: '100%', label: 'Automated' }
  ];

  return (
    <div className="min-h-screen gradient-mesh">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-spyne-400 to-spyne-600 flex items-center justify-center">
              <Car className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Clone Spyne
            </span>
          </Link>
          
          <div className="flex items-center gap-6">
            <Link 
              href="/vehicles" 
              className="text-gray-400 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link 
              href="/capture"
              className="px-5 py-2.5 rounded-lg bg-spyne-600 hover:bg-spyne-500 text-white font-medium transition-colors"
            >
              Start Capture
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-spyne-500/10 border border-spyne-500/20 text-spyne-400 text-sm mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Photography
              </div>
              
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight mb-6">
                Professional
                <span className="block bg-gradient-to-r from-spyne-400 via-purple-400 to-spyne-400 bg-200% animate-gradient bg-clip-text text-transparent">
                  360° Car Photos
                </span>
                in Minutes
              </h1>
              
              <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                Transform any location into a professional studio. Our AI removes backgrounds, 
                adds realistic shadows, and creates stunning 360° spin views automatically.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Link
                  href="/capture"
                  className="group flex items-center gap-3 px-6 py-3.5 rounded-xl bg-gradient-to-r from-spyne-500 to-spyne-600 hover:from-spyne-400 hover:to-spyne-500 text-white font-semibold transition-all glow"
                >
                  <Camera className="w-5 h-5" />
                  Start Capturing
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                
                <button className="flex items-center gap-3 px-6 py-3.5 rounded-xl border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-all">
                  <Play className="w-5 h-5" />
                  Watch Demo
                </button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-6 mt-12 pt-8 border-t border-gray-800">
                {stats.map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + i * 0.1 }}
                  >
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    <div className="text-sm text-gray-500">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Right: 3D Car Preview */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
            >
              <div className="relative aspect-[4/3] rounded-2xl overflow-hidden glass glow-purple">
                {/* Gradient background */}
                <div className="absolute inset-0 bg-gradient-to-b from-gray-800/50 to-gray-900/50" />
                
                {/* Grid pattern */}
                <div className="absolute inset-0 grid-pattern opacity-50" />
                
                {/* Car placeholder */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    animate={{ 
                      rotateY: isHovered ? 15 : 0,
                      scale: isHovered ? 1.05 : 1
                    }}
                    transition={{ duration: 0.4 }}
                    className="relative"
                  >
                    <div className="w-80 h-48 rounded-xl bg-gradient-to-br from-slate-700 to-slate-800 shadow-2xl flex items-center justify-center">
                      <Car className="w-24 h-24 text-gray-600" />
                    </div>
                    
                    {/* Rotation indicator */}
                    <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 text-gray-500 text-sm">
                      <RotateCcw className={`w-4 h-4 ${isHovered ? 'animate-spin-slow' : ''}`} />
                      <span>Drag to rotate</span>
                    </div>
                  </motion.div>
                </div>

                {/* Floating badges */}
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="absolute top-6 right-6 px-3 py-1.5 rounded-full bg-green-500/20 border border-green-500/30 text-green-400 text-sm flex items-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  AI Processed
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              Everything You Need for
              <span className="text-spyne-400"> Pro Photos</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Complete toolkit for automotive photography, powered by the same 
              AI technology as industry leaders.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group p-6 rounded-2xl bg-gray-900/50 border border-gray-800 hover:border-spyne-500/50 transition-all card-hover"
              >
                <div className="w-12 h-12 rounded-xl bg-spyne-500/10 flex items-center justify-center mb-4 group-hover:bg-spyne-500/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-spyne-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative rounded-3xl overflow-hidden"
          >
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-spyne-600 to-purple-600" />
            <div className="absolute inset-0 grid-pattern opacity-20" />
            
            {/* Content */}
            <div className="relative p-12 text-center">
              <h2 className="text-3xl lg:text-4xl font-bold mb-4">
                Ready to Transform Your Vehicle Photos?
              </h2>
              <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
                Join thousands of dealerships using AI-powered photography 
                to sell cars faster.
              </p>
              <Link
                href="/vehicles"
                className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-white text-gray-900 font-semibold hover:bg-gray-100 transition-colors"
              >
                Go to Dashboard
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-800">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-spyne-400 to-spyne-600 flex items-center justify-center">
              <Car className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold">Clone Spyne</span>
          </div>
          
          <p className="text-gray-500 text-sm">
            Open-source alternative to Spyne. Built with ❤️
          </p>
          
          <div className="flex items-center gap-4 text-gray-400 text-sm">
            <Globe className="w-4 h-4" />
            <span>Free & Open Source</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

