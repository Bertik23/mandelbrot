import pygame
import aiohttp  # instead of requests
import asyncio
import getpass
pygame.init()

blob_yposition = 30
blob_yspeed = 0
achievement = False

gravity = 1

screen_size = 640, 480
screen = pygame.display.set_mode(screen_size)

clock = pygame.time.Clock()
running = True
flying_frames = 0
best = 0
color = (50, 50, 50)
font = pygame.font.SysFont(
    "Helvetica Neue,Helvetica,Ubuntu Sans,Bitstream Vera Sans,DejaVu Sans,"
    "Latin Modern Sans,Liberation Sans,Nimbus Sans L,Noto Sans,Calibri,Futura"
    ",Beteckna,Arial",
    16)

# NEW CODE
loop = asyncio.get_event_loop()


async def post_achievement():
    # Note that it says "async def",
    # post_achievement() creates a coroutine that you can't run directly
    # you have to create a task in an event loop to run it
    payload = dict(name=getpass.getuser(),
                   title="ten seconds",
                   subtitle="last for ten seconds without touching the ground")

    async with aiohttp.ClientSession() as session:

        # await returns the control flow to the event loop
        # until there is data available
        response = await session.post(
            'http://httpbin.org/post',
            data=payload)

    if response.status == 200:
        print("achievement posted")

        # await again, maybe response body is large
        body = await response.read()
        print(body)
        return body
    else:
        print("something went wrong")


def run_once(loop):
    loop.call_soon(loop.stop)
    loop.run_forever()


while running:
    clock.tick(30)

    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_UP:
            blob_yspeed += 10

    # ...
    # move sprites around, collision detection, etc

    blob_yposition += blob_yspeed
    blob_yspeed -= gravity

    if blob_yposition <= 30:
        blob_yspeed = 0
        blob_yposition = 30
        flying_frames = 0
    else:
        flying_frames += 1
    if flying_frames > best:
        best = flying_frames

    # 300 frames=10 seconds
    if not achievement and best > 300:
        # NEW CODE
        # Create coroutines and add them to the event loop as tasks
        # This does not actually run the coroutines yet!
        for i in range(10):
            loop.create_task(post_achievement())

        achievement = True
        color = (100, 0, 0)

    if blob_yposition > 480:
        blob_yposition = 480
        blob_yspeed = -1 * abs(blob_yspeed)

    # ...
    # draw

    screen.fill((255, 255, 255))

    pygame.draw.rect(screen, color,
                     pygame.Rect(screen_size[0] / 2,
                                 screen_size[1] - blob_yposition,
                                 18, 25))
    fps = clock.get_fps()

    # NEW CODE
    # display number of currently running tasks in event loop
    ntasks = len(asyncio.all_tasks(loop))
    message = (f"current:{flying_frames//30},   "
               f"best:{best//30},   fps:{fps:.2f},   tasks:{ntasks}")
    surf = font.render(message, True, (0, 0, 0))
    screen.blit(surf, (0, 0))
    pygame.display.update()

    # tell event loop to run once
    # if there are no i/o events, this might return right away
    # if there are events or tasks that don't need to wait for i/o, then
    # run ONE task until the next "await" statement
    run_once(loop)
    # we run this *after* display.update(), but *before*
    # clock.tick(fps) and getting input events. This way i/o only eats
    # into the time when clock.tick(fps) would wait anyway.

while len(asyncio.all_tasks(loop)):
    run_once(loop)
loop.shutdown_asyncgens()
loop.close()
print("Thank you for playing!")
