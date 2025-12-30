# app/utils/filters.py

def chunk_list(seq, size):
#----Yield successive size-sized chunks from seq
  return [seq[i:i + size] for i in range(0, len(seq), size)]


