import edge_tts

async def generate_audio(text, outputFilename):
    # Wrapping the text in SSML tags to reduce the speech rate to 75% (25% slower)
    ssml_text = f'<speak><prosody rate="-25%">{text}</prosody></speak>'
    
    # Generating the audio with the modified SSML text
    communicate = edge_tts.Communicate(ssml_text, "en-AU-WilliamNeural")
    await communicate.save(outputFilename)
