import os
import logging
import click
from video_extraction import process_mkv_file
from audio_transcription import process_audio_files
from transcript_merger import process_transcripts
from summarize_transcript import (
    load_transcript, prepare_transcript_for_summary, 
    generate_summary, save_summary, estimate_tokens_and_price
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """OBS Video Processing CLI"""
    pass

@cli.command()
@click.argument('input_video', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--mic-track', default=3, help='Track number for microphone audio (default: 3)')
@click.option('--desktop-track', default=2, help='Track number for desktop audio (default: 2)')
def extract_audio(input_video, output_dir, mic_track, desktop_track):
    """Extract audio tracks from MKV file."""
    try:
        audio_files = process_mkv_file(input_video, output_dir, mic_track_number=mic_track, desktop_track_number=desktop_track)
        click.echo(f"Audio files extracted: {audio_files}")
    except Exception as e:
        logger.error(f"Audio extraction failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('mic_audio', type=click.Path(exists=True))
@click.argument('desktop_audio', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
def transcribe(mic_audio, desktop_audio, output_dir):
    """Transcribe audio files."""
    try:
        transcriptions = process_audio_files(mic_audio, desktop_audio, output_dir)
        click.echo(f"Transcriptions created: {transcriptions}")
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('mic_transcript', type=click.Path(exists=True))
@click.argument('desktop_transcript', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def merge_transcripts(mic_transcript, desktop_transcript, output_file):
    """Merge microphone and desktop transcripts."""
    try:
        process_transcripts(mic_transcript, desktop_transcript, output_file)
        click.echo(f"Merged transcript saved to: {output_file}")
    except Exception as e:
        logger.error(f"Transcript merging failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('merged_transcript', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--model', type=click.Choice(['claude-3-5-sonnet', 'claude-3-haiku']), default='claude-3-5-sonnet', help='Model to use for summarization')
@click.option('--dry-run', is_flag=True, help='Estimate tokens and price without generating summary')
def summarize(merged_transcript, output_file, model, dry_run):
    """Generate summary from merged transcript."""
    try:
        transcript_data = load_transcript(merged_transcript)
        transcript_text = prepare_transcript_for_summary(transcript_data)
        
        total_tokens, estimated_price = estimate_tokens_and_price(transcript_text, model)
        click.echo(f"Estimated tokens: {total_tokens}")
        click.echo(f"Estimated price: ${estimated_price:.4f}")
        
        if dry_run:
            click.echo("Dry run completed. No summary generated.")
            return
        
        summary = generate_summary(transcript_text, model_name=model)
        save_summary(summary, output_file)
        click.echo(f"Summary saved to: {output_file}")
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('input_video', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--mic-track', default=3, help='Track number for microphone audio (default: 3)')
@click.option('--desktop-track', default=2, help='Track number for desktop audio (default: 2)')
@click.option('--model', type=click.Choice(['claude-3-5-sonnet', 'claude-3-haiku']), default='claude-3-5-sonnet', help='Model to use for summarization')
def process_all(input_video, output_dir, mic_track, desktop_track, model):
    """Run the entire video processing workflow."""
    try:
        # Step 1: Process MKV file
        click.echo("Step 1: Processing MKV file")
        audio_files = process_mkv_file(input_video, output_dir, mic_track_number=mic_track, desktop_track_number=desktop_track)
        
        # Step 2: Transcribe audio files
        click.echo("Step 2: Transcribing audio files")
        transcriptions = process_audio_files(audio_files['microphone'], audio_files['desktop'], output_dir)
        
        # Step 3: Merge transcripts
        click.echo("Step 3: Merging transcripts")
        merged_transcript_file = os.path.join(output_dir, "merged_transcript.json")
        process_transcripts(transcriptions['microphone'], transcriptions['desktop'], merged_transcript_file)
        
        # Step 4: Generate summary
        click.echo("Step 4: Generating summary")
        transcript_data = load_transcript(merged_transcript_file)
        transcript_text = prepare_transcript_for_summary(transcript_data)
        
        total_tokens, estimated_price = estimate_tokens_and_price(transcript_text, model)
        click.echo(f"Estimated tokens for summary: {total_tokens}")
        click.echo(f"Estimated price for summary: ${estimated_price:.4f}")
        
        summary = generate_summary(transcript_text, model_name=model)
        
        # Save summary
        summary_file = os.path.join(output_dir, "meeting_summary.txt")
        save_summary(summary, summary_file)
        
        click.echo(f"Workflow completed successfully. Summary saved to: {summary_file}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    cli()
