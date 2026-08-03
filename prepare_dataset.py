from datasets import load_dataset
from pathlib import Path
import soundfile as sf
import librosa
import pandas as pd
from tqdm import tqdm

OUT = Path("dataset")
OUT.mkdir(exist_ok=True)

WAVS = OUT / "wavs"
WAVS.mkdir(exist_ok=True)

print("Ucitavam Common Voice...")

dataset = load_dataset(
    "mozilla-foundation/common_voice_22_0",
    "sr",
    split="train",
    trust_remote_code=True
)

metadata = []

for i, sample in enumerate(tqdm(dataset)):
    text = sample["sentence"].strip()

    audio = sample["audio"]

    samples = audio["array"]
    sr = audio["sampling_rate"]

    samples = librosa.resample(
        samples,
        orig_sr=sr,
        target_sr=22050
    )

    filename = f"{i:07d}.wav"

    sf.write(
        WAVS / filename,
        samples,
        22050
    )

    metadata.append({
        "file_name": filename,
        "text": text
    })

df = pd.DataFrame(metadata)

df.to_csv(
    OUT / "metadata.csv",
    sep="|",
    index=False,
    header=False
)

print("Gotovo.")