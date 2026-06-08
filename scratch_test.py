import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.providers.deepgram_stt import DeepgramSTT
from tests.test_providers import _make_listen_results, _FakeConnectCm, _pcm_chunks

async def main():
    print("Starting test_partial_before_final replica...")
    partial = _make_listen_results(text="hel", is_final=False)
    final = _make_listen_results(text="hello", is_final=True, confidence=0.91)

    recv_queue = [partial, final]

    def _recv_messages():
        print(f"recv_messages called, queue len: {len(recv_queue)}")
        if recv_queue:
            return recv_queue.pop(0)
        print("raising TimeoutError in recv_messages")
        raise TimeoutError()

    mock_socket = AsyncMock()
    mock_socket.recv = AsyncMock(side_effect=_recv_messages)
    mock_socket.send_media = AsyncMock()
    mock_socket.send_finalize = AsyncMock()
    mock_socket.send_close_stream = AsyncMock()

    mock_client = MagicMock()
    mock_client.listen.v1.connect = MagicMock(
        return_value=_FakeConnectCm(mock_socket)
    )

    stt = DeepgramSTT()
    with (
        patch(
            "app.providers.deepgram_stt.AsyncDeepgramClient",
            return_value=mock_client,
        ),
        patch("app.providers.deepgram_stt.get_settings") as mock_settings,
    ):
        mock_settings.return_value.deepgram_api_key = "test-key"
        await stt.connect("en")
        print("Connected.")
        
        # Let's run stream and print each yielded transcript
        async for transcript in stt.stream(_pcm_chunks(b"\x00\x00" * 320)):
            print(f"Yielded: {transcript}")
            
        print("Stream completed, closing STT...")
        await stt.close()
        print("STT closed.")

if __name__ == "__main__":
    asyncio.run(main())
