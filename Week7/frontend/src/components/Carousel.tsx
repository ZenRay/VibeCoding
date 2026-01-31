import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react';
import type { Slide } from '../types';

interface CarouselProps {
  slides: Slide[];
  isOpen: boolean;
  onClose: () => void;
  initialIndex?: number;
}

export const Carousel: React.FC<CarouselProps> = ({
  slides,
  isOpen,
  onClose,
  initialIndex = 0,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const AUTOPLAY_INTERVAL = 5000; // 5 seconds

  // Reset index when opening
  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(initialIndex);
      setIsPlaying(true);
    }
  }, [isOpen, initialIndex]);

  // Navigate to next slide
  const goToNext = useCallback(() => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex((prev) => (prev + 1) % slides.length);
    setTimeout(() => setIsTransitioning(false), 300);
  }, [slides.length, isTransitioning]);

  // Navigate to previous slide
  const goToPrevious = useCallback(() => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex((prev) => (prev - 1 + slides.length) % slides.length);
    setTimeout(() => setIsTransitioning(false), 300);
  }, [slides.length, isTransitioning]);

  // Jump to specific slide
  const goToSlide = useCallback((index: number) => {
    if (isTransitioning || index === currentIndex) return;
    setIsTransitioning(true);
    setCurrentIndex(index);
    setTimeout(() => setIsTransitioning(false), 300);
  }, [currentIndex, isTransitioning]);

  // Toggle play/pause
  const togglePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  // Auto-advance timer
  useEffect(() => {
    if (!isOpen || !isPlaying || slides.length <= 1) return;

    const timer = setInterval(() => {
      goToNext();
    }, AUTOPLAY_INTERVAL);

    return () => clearInterval(timer);
  }, [isOpen, isPlaying, slides.length, goToNext]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'ArrowRight':
          goToNext();
          break;
        case ' ':
          e.preventDefault();
          togglePlayPause();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, goToPrevious, goToNext, togglePlayPause]);

  if (!isOpen || slides.length === 0) return null;

  const currentSlide = slides[currentIndex];

  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-sm"
        title="退出全屏 (ESC)"
      >
        <X className="w-6 h-6" />
      </button>

      {/* Play/Pause Button */}
      <button
        onClick={togglePlayPause}
        className="absolute top-4 right-16 z-10 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-sm"
        title={isPlaying ? '暂停 (Space)' : '播放 (Space)'}
      >
        {isPlaying ? (
          <Pause className="w-6 h-6" />
        ) : (
          <Play className="w-6 h-6" />
        )}
      </button>

      {/* Main Content */}
      <div className="h-full flex items-center justify-center p-8">
        <div
          className={`w-full h-full flex flex-col items-center justify-center transition-opacity duration-300 ${
            isTransitioning ? 'opacity-0' : 'opacity-100'
          }`}
        >
          {/* Image */}
          {currentSlide.image_path ? (
            <div className="flex-1 flex items-center justify-center w-full max-w-6xl">
              <img
                src={`http://localhost:8000/${currentSlide.image_path}`}
                alt={`幻灯片 ${currentIndex + 1}`}
                className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center w-full max-w-6xl">
              <div className="text-white/50 text-center">
                <div className="text-6xl mb-4">📄</div>
                <p className="text-xl">暂无图片</p>
              </div>
            </div>
          )}

          {/* Text Content */}
          {currentSlide.text && (
            <div className="mt-8 max-w-4xl text-center">
              <p className="text-white text-2xl leading-relaxed whitespace-pre-wrap">
                {currentSlide.text}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Arrows */}
      {slides.length > 1 && (
        <>
          <button
            onClick={goToPrevious}
            disabled={isTransitioning}
            className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm"
            title="上一张 (←)"
          >
            <ChevronLeft className="w-8 h-8" />
          </button>

          <button
            onClick={goToNext}
            disabled={isTransitioning}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm"
            title="下一张 (→)"
          >
            <ChevronRight className="w-8 h-8" />
          </button>
        </>
      )}

      {/* Bottom Controls */}
      <div className="absolute bottom-8 left-0 right-0 flex flex-col items-center gap-4">
        {/* Page Indicator Dots */}
        {slides.length > 1 && (
          <div className="flex gap-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-2 h-2 rounded-full transition-all ${
                  index === currentIndex
                    ? 'bg-white w-8'
                    : 'bg-white/40 hover:bg-white/60'
                }`}
                title={`跳转到第 ${index + 1} 张`}
              />
            ))}
          </div>
        )}

        {/* Page Counter */}
        <div className="text-white/80 text-sm font-medium backdrop-blur-sm bg-black/30 px-4 py-2 rounded-full">
          {currentIndex + 1} / {slides.length}
        </div>
      </div>

      {/* Keyboard Hints (shown briefly on open) */}
      <div className="absolute bottom-24 left-1/2 -translate-x-1/2 text-white/60 text-xs text-center animate-fadeIn">
        <p>← → 切换 | Space 暂停/播放 | ESC 退出</p>
      </div>
    </div>
  );
};
