use tauri_app_lib::audio::buffer::AudioBuffer;
use tauri_app_lib::audio::resampler::{AudioResampler, ResamplerConfig};
use tauri_app_lib::network::protocol::{ClientMessage, ConnectionConfig, ServerMessage};

#[test]
fn audio_resample_and_protocol_roundtrip() {
    let config = ConnectionConfig {
        endpoint: "wss://api.elevenlabs.io/v1/speech-to-text/realtime".to_string(),
        api_key: "test-key".to_string(),
        model_id: "scribe_v2_realtime".to_string(),
        audio_format: "pcm_16000".to_string(),
        sample_rate: 16_000,
        commit_strategy: "vad".to_string(),
        language_code: None,
        proxy_url: None,
    };
    let url = config.build_url();
    assert!(url.contains("model_id=scribe_v2_realtime"));

    let buffer = AudioBuffer::new(16_000);
    for _ in 0..160 {
        buffer.push(0.1);
    }
    let mut captured = vec![0.0f32; 160];
    let read = buffer.pop_batch(&mut captured);
    assert!(read > 0);

    let mut resampler = AudioResampler::new(ResamplerConfig {
        input_rate: 48_000,
        output_rate: 16_000,
        chunk_size: 480,
    })
    .expect("resampler");
    let resampled = resampler.process(&vec![0.1; 480]).expect("resample");
    assert!(!resampled.is_empty());

    let pcm: Vec<i16> = resampled
        .iter()
        .map(|s| (s.clamp(-1.0, 1.0) * i16::MAX as f32) as i16)
        .collect();
    let msg = ClientMessage::audio_chunk(&pcm, 16_000).expect("audio chunk");
    let json = msg.to_json().expect("serialize");
    assert!(json.contains("input_audio_chunk"));
    assert!(json.contains("audio_base_64"));

    let server =
        ServerMessage::from_json(r#"{"message_type":"partial_transcript","text":"hello world"}"#)
    .expect("parse");
    match server {
        ServerMessage::PartialTranscript { text } => assert_eq!(text, "hello world"),
        _ => panic!("unexpected message"),
    }
}
