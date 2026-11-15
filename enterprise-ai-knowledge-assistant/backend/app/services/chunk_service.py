
def split_text(
    text:str,
    chunk_size:int=1000,
    chunk_overlap:int=150,
):
    if chunk_size<=0:
        raise ValueError("Chunk size must be positive")

    if chunk_overlap<0 or chunk_overlap>=chunk_size:
        raise ValueError("Overlap must be non-negative and smaller than chunk size")

    chunks=[]
    start=0

    while start<len(text):
        end=start+chunk_size
        chunk=text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start+=chunk_size-chunk_overlap

    return chunks
