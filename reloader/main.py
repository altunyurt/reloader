from asyncinotify import Inotify, Mask
from typing import Callable, Any, Optional, Awaitable
import asyncio
import click
import pathlib
import os


WFlags = Mask.CREATE | Mask.MOVE | Mask.DELETE | Mask.MODIFY | Mask.CLOSE_WRITE


async def monitor(path, event: asyncio.Event):
    with Inotify() as ntf:
        ntf.add_watch(pathlib.Path(path), WFlags)
        async for e in ntf:
            # bir anlamda tekilliyoruz eventleri
            if not event.is_set():
                event.set()


async def stream_output(stream, prefix):
    """Stream output from subprocess without blocking"""
    try:
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"[{prefix}] {line.decode().strip()}")
    except Exception as e:
        print(f"Error streaming {prefix}: {e}")


async def debug_process_state(process):
    if process is None:
        print("No process")
        return

    print(f"Process PID: {process.pid}")
    print(f"Return code: {process.returncode}")

    try:
        # Check if process is actually running
        os.kill(process.pid, 0)  # Send signal 0 (no-op, just checks if alive)
        print("Process is alive")
    except ProcessLookupError:
        print("Process is dead")
    except PermissionError:
        print("Process exists but we can't signal it")


async def run(args, event: asyncio.Event):
    print("Executing...")
    process = None
    stdout_task = None
    stderr_task = None

    while True:
        await event.wait()

        # Kill previous process
        if process and process.returncode is None:
            if stdout_task:
                stdout_task.cancel()
            if stderr_task:
                stderr_task.cancel()

            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
        stdout_task = asyncio.create_task(stream_output(process.stdout, "OUT"))
        stderr_task = asyncio.create_task(stream_output(process.stderr, "ERR"))

        event.clear()


async def tgrun(args, path):
    event = asyncio.Event()
    event.set()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run(args, event))
        tg.create_task(monitor(path, event))


@click.command()
@click.option("-p", "--path", default=".", help="Path")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def main(path, args):
    asyncio.run(tgrun(args, path))


if __name__ == "__main__":
    main()
