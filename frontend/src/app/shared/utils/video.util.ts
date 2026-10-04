export function toEmbedUrl(videoUrl: string, provider: string): string | null {
  if (!videoUrl) {
    return null;
  }

  if (provider === 'YOUTUBE' || videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
    const match =
      videoUrl.match(/[?&]v=([^&]+)/) ||
      videoUrl.match(/youtu\.be\/([^?&]+)/) ||
      videoUrl.match(/embed\/([^?&]+)/);
    return match ? `https://www.youtube.com/embed/${match[1]}` : null;
  }

  if (provider === 'VIMEO' || videoUrl.includes('vimeo.com')) {
    const match = videoUrl.match(/vimeo\.com\/(?:video\/)?(\d+)/);
    return match ? `https://player.vimeo.com/video/${match[1]}` : null;
  }

  return null;
}
