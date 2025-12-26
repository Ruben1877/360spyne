'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Car, 
  Plus, 
  Search, 
  Filter, 
  Grid3X3, 
  List,
  RefreshCw,
  Camera
} from 'lucide-react';
import VehicleCard from '@/components/VehicleCard';

interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  type: string;
  status: 'pending' | 'capturing' | 'processing' | 'completed';
  images: any[];
  createdAt: string;
}

// Demo vehicles for development
const DEMO_VEHICLES: Vehicle[] = [
  {
    id: '1',
    make: 'BMW',
    model: 'M4 Competition',
    year: 2024,
    type: 'coupe',
    status: 'completed',
    images: Array(8).fill(null).map((_, i) => ({
      id: `1-${i}`,
      angleIndex: i,
      processedUrl: `https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800&h=600&fit=crop`,
      status: 'completed'
    })),
    createdAt: new Date().toISOString()
  },
  {
    id: '2',
    make: 'Porsche',
    model: '911 Carrera',
    year: 2023,
    type: 'coupe',
    status: 'processing',
    images: Array(8).fill(null).map((_, i) => ({
      id: `2-${i}`,
      angleIndex: i,
      status: i < 5 ? 'completed' : 'processing'
    })),
    createdAt: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '3',
    make: 'Mercedes-Benz',
    model: 'AMG GT',
    year: 2024,
    type: 'coupe',
    status: 'capturing',
    images: Array(8).fill(null).map((_, i) => ({
      id: `3-${i}`,
      angleIndex: i,
      status: i < 3 ? 'uploaded' : 'pending'
    })),
    createdAt: new Date(Date.now() - 172800000).toISOString()
  },
  {
    id: '4',
    make: 'Tesla',
    model: 'Model S Plaid',
    year: 2024,
    type: 'sedan',
    status: 'pending',
    images: Array(8).fill(null).map((_, i) => ({
      id: `4-${i}`,
      angleIndex: i,
      status: 'pending'
    })),
    createdAt: new Date(Date.now() - 259200000).toISOString()
  }
];

export default function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>(DEMO_VEHICLES);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Filter vehicles
  const filteredVehicles = vehicles.filter(vehicle => {
    const matchesSearch = 
      `${vehicle.make} ${vehicle.model} ${vehicle.year}`
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
    
    const matchesStatus = 
      statusFilter === 'all' || vehicle.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const statusOptions = [
    { value: 'all', label: 'All Vehicles' },
    { value: 'pending', label: 'Pending' },
    { value: 'capturing', label: 'Capturing' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' }
  ];

  const stats = {
    total: vehicles.length,
    completed: vehicles.filter(v => v.status === 'completed').length,
    processing: vehicles.filter(v => v.status === 'processing').length,
    pending: vehicles.filter(v => v.status === 'pending' || v.status === 'capturing').length
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a]">
      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-spyne-400 to-spyne-600 flex items-center justify-center">
                <Car className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Vehicles</h1>
                <p className="text-xs text-gray-500">Inventory Dashboard</p>
              </div>
            </Link>

            <div className="flex items-center gap-3">
              <Link
                href="/capture"
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-spyne-600 hover:bg-spyne-500 text-white font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                Add Vehicle
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Vehicles', value: stats.total, color: 'text-white' },
            { label: 'Completed', value: stats.completed, color: 'text-green-400' },
            { label: 'Processing', value: stats.processing, color: 'text-blue-400' },
            { label: 'Pending', value: stats.pending, color: 'text-yellow-400' }
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="p-4 rounded-xl bg-gray-900/50 border border-gray-800"
            >
              <p className="text-gray-500 text-sm">{stat.label}</p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                placeholder="Search vehicles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-gray-900 border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-spyne-500 transition-colors"
              />
            </div>
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2.5 rounded-lg bg-gray-900 border border-gray-800 text-white focus:outline-none focus:border-spyne-500 transition-colors"
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* View toggle */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-gray-900 border border-gray-800">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'grid' ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-white'
              }`}
            >
              <Grid3X3 className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list' ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-white'
              }`}
            >
              <List className="w-5 h-5" />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={() => {}}
            disabled={isLoading}
            className="p-2.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-400 hover:text-white hover:border-gray-700 transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Vehicle grid */}
        {filteredVehicles.length > 0 ? (
          <div className={`grid gap-6 ${
            viewMode === 'grid' 
              ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' 
              : 'grid-cols-1'
          }`}>
            {filteredVehicles.map((vehicle, index) => (
              <VehicleCard key={vehicle.id} vehicle={vehicle} index={index} />
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
              <Car className="w-8 h-8 text-gray-600" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No vehicles found</h3>
            <p className="text-gray-500 mb-6">
              {searchQuery || statusFilter !== 'all' 
                ? 'Try adjusting your filters'
                : 'Add your first vehicle to get started'}
            </p>
            <Link
              href="/capture"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-spyne-600 hover:bg-spyne-500 text-white font-medium transition-colors"
            >
              <Camera className="w-5 h-5" />
              Start Capture
            </Link>
          </motion.div>
        )}
      </main>
    </div>
  );
}

