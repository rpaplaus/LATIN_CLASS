export interface TTSResponse {
  audio_hash: string;
  audio_url: string;
  audio_base64: string;
  cached: boolean;
  text: string;
  voice: string;
}
