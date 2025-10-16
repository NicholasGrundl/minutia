from tests.scripts.generate_test_fixtures import FixtureGenerator
  from pathlib import Path
  import json

  # Initialize the generator
  generator = FixtureGenerator(
      recordings_dir=Path('+recordings'),
      output_dir=Path('tests')
  )

  # List available recordings
  print("Available recordings:")
  available = generator.list_available_recordings()

  # Create specific fixtures from the example files
  fixtures_metadata = []

  # 1. Short microphone test (5 seconds)
  metadata = generator.create_fixture_set(
      source_mkv='Example-Microphone.mkv',
      output_name='microphone_5s',
      start_seconds=1.0,
      duration_seconds=5.0,
      description='Clear microphone audio, short duration'
  )
  fixtures_metadata.append(metadata)

  # 2. Noisy sample (10 seconds) 
  metadata = generator.create_fixture_set(
      source_mkv='Example-Noisy.mkv',
      output_name='noisy_10s',
      start_seconds=2.0,
      duration_seconds=10.0,
      description='Background noise and audio artifacts'
  )
  fixtures_metadata.append(metadata)

  # 3. Podcast sample (15 seconds)
  metadata = generator.create_fixture_set(
      source_mkv='Example-Podcast.mkv',
      output_name='podcast_15s',
      start_seconds=5.0,
      duration_seconds=15.0,
      description='Clear speech, podcast-style audio'
  )
  fixtures_metadata.append(metadata)

  # 4. Song + speech mix (20 seconds)
  metadata = generator.create_fixture_set(
      source_mkv='Example-Song+MLKSpeech.mkv',
      output_name='mixed_audio_20s',
      start_seconds=10.0,
      duration_seconds=20.0,
      description='Music and speech overlapping'
  )
  fixtures_metadata.append(metadata)

  # Save all metadata
  generator.save_metadata(fixtures_metadata)

  print(f"\nCreated {len(fixtures_metadata)} fixtures:")
  for fixture in fixtures_metadata:
      print(f"  - {fixture['name']}: {fixture['description']}")

  print(f"\nFixtures saved to: {generator.fixtures_dir}")
  print(f"Metadata saved to: {generator.metadata_file}")

  If you want to see what got created, you can also run:

  # Check what fixtures were created
  import json

  # Load and display metadata
  with open(generator.metadata_file) as f:
      metadata = json.load(f)

  print(json.dumps(metadata, indent=2))

  # List created files
  print("\nVideo fixtures:")
  for p in generator.video_dir.glob("*.mkv"):
      print(f"  {p}")

  print("\nAudio fixtures:")
  for p in generator.audio_dir.glob("**/*.wav"):
      print(f"  {p}")