/*
 * Exact-build field and actor dialogue art hooks for overlay 36 in the IREO
 * ROM fingerprint guarded by dialogue_art_patch.py. These addresses and
 * layouts are not portable to another game revision.
 */
#include <stdint.h>
#include <stddef.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;
typedef struct BmpWin BmpWin;
typedef struct GFLBitmap GFLBitmap;

typedef BmpWin *(*BmpWinCreateDynamicFn)(u8, u8, u8, u8, u8, u8, u8);
typedef void (*BmpWinFreeFn)(BmpWin *);
typedef void (*BmpWinFlushFn)(BmpWin *);
typedef void (*BmpWinClearScreenFn)(BmpWin *);
typedef GFLBitmap *(*BmpWinGetBitmapFn)(BmpWin *);
typedef GFLBitmap *(*LoadBitmapFn)(u32, u32, u32, u32);
typedef void (*LoadNclrFn)(u32, u32, u32, u32, u32, u32, u32);
typedef void (*BitmapFillFn)(GFLBitmap *, u8);
typedef void (*BitmapCopyAreaFn)(GFLBitmap *, GFLBitmap *, u32, u32, s32, s32, u32, u32, u16);
typedef void (*BitmapFreeFn)(GFLBitmap *);
typedef void (*LoadScreenFn)(u32);
typedef void (*HeapFreeFn)(void *);
typedef BmpWin *(*GetTalkBmpFn)(void *, u32);
typedef void *(*GetActorWorkFn)(void *);
typedef void *(*GetActorSystemFn)(void *);
typedef void *(*FindFieldActorFn)(void *, u16);

#define GAME_FN(type, address) ((type)(uintptr_t)((address) | 1u))
#define FIELD_ART_OFFSET 0x20
#define ACTOR_ART_OFFSET 0x28
#define ACTOR_PROFILE_OFFSET 0x2c
#define FIELD_ART_MIN_Y 17
#define FIELD_ART_NCGR 12
#define FIELD_ART_NCLR 13
#define FIELD_ART_PALETTE 15
#define ACTOR_ART_BG 2
#define ACTOR_ART_PALETTE 14
#define ACTOR_TEXT_BG 1
#define ACTOR_TEXT_PALETTE 15
#define ACTOR_BLEND_OFFSET 0x30
#define TALK_SYS_WINDOWS_OFFSET 0x18
#define TALK_WIN_STRIDE 0x64
#define TALK_WIN_BMP_OFFSET 0x0c
#define TALK_WIN_SKIP_ANIM_OFFSET 0x02
#define TALK_WIN_FRAME_TYPE_OFFSET 0x03
#define TALK_WIN_SHAPE_OFFSET 0x04
#define TALK_WIN_TEXT_X_OFFSET 0x5c
#define TALK_WIN_TEXT_Y_OFFSET 0x5d
#define ACTOR_TEXT_X 0
#define ACTOR_TEXT_Y 0
#define ACTOR_TEXT_WINDOW_X 1
#define ACTOR_TEXT_WINDOW_Y 20
#define ACTOR_TEXT_WINDOW_WIDTH 30
#define ACTOR_TEXT_WINDOW_HEIGHT 4
#define PROFILE_WILDCARD 0xffff

typedef struct {
    u16 zoneId;
    u16 uid;
    u16 ncgr;
    u16 nclr;
} DialogueSpeakerProfile;

#include "dialogue_speaker_profiles.inc"

typedef struct {
    BmpWin *window;
    void *stream;
    void *printer;
    void *msgData;
    void *strbuf;
    void *sys;
    u8 cursor[8];
} FieldMsgWin;

typedef struct {
    u8 unk0;
    u8 type;
    s16 shake;
    void *strbuf;
    void *talk;
    u8 cursor[8];
    void *sys;
    const void *posSource;
    u8 pos[12];
    u8 unused[12];
} ActorMsgWin;

_Static_assert(sizeof(FieldMsgWin) == 0x20, "stock FieldMsgWin layout changed");
_Static_assert(sizeof(ActorMsgWin) == 0x34, "stock ActorMsgWin layout changed");
_Static_assert(offsetof(ActorMsgWin, unused) == ACTOR_ART_OFFSET, "actor extension moved");

static void clear_and_free_window(BmpWin *window, u32 bg) {
    if (window != 0) {
        GAME_FN(BmpWinClearScreenFn, 0x020484b4)(window);
        GAME_FN(LoadScreenFn, 0x02044f90)(bg);
        GAME_FN(BmpWinFreeFn, 0x02048210)(window);
    }
}

static void restore_stock_field_window(FieldMsgWin *win) {
    GFLBitmap *bitmap = GAME_FN(BmpWinGetBitmapFn, 0x020484f4)(win->window);
    GAME_FN(BitmapFillFn, 0x0204713c)(bitmap, 0xff);
    GAME_FN(BmpWinFlushFn, 0x0204826c)(win->window);
    GAME_FN(BmpWinFlushFn, 0x02048244)(win->window);
    ((void (*)(BmpWin *))(uintptr_t)(0x02189f2c | 1u))(win->window);
}

static BmpWin *create_art_window(void *sys, u32 bg, u32 palette, u32 ncgr, u32 nclr,
                                 u32 x, u32 y, u32 width, u32 height) {
    u16 heapId = *(u16 *)sys;
    BmpWin *window = GAME_FN(BmpWinCreateDynamicFn, 0x020480c0)(bg, x, y, width, height, palette, 1);
    GFLBitmap *source;
    GFLBitmap *destination;

    if (window == 0) {
        return 0;
    }
    source = GAME_FN(LoadBitmapFn, 0x02046f3c)(5, ncgr, 0, heapId);
    if (source == 0) {
        GAME_FN(BmpWinFreeFn, 0x02048210)(window);
        return 0;
    }

    GAME_FN(LoadNclrFn, 0x0204b0f0)(5, nclr, 0, 0, palette * 0x20, 0x20, heapId);
    destination = GAME_FN(BmpWinGetBitmapFn, 0x020484f4)(window);
    GAME_FN(BitmapFillFn, 0x0204713c)(destination, 0);
    GAME_FN(BitmapCopyAreaFn, 0x02047008)(source, destination, 0, 0, 0, 0, 256, 160, 0);
    GAME_FN(BmpWinFlushFn, 0x0204826c)(window);
    GAME_FN(BmpWinFlushFn, 0x02048244)(window);
    GAME_FN(LoadScreenFn, 0x02044f90)(bg);
    GAME_FN(BitmapFreeFn, 0x02046edc)(source);
    return window;
}

void dialogue_attach_art(FieldMsgWin *win, void *sys, u32 y) {
    BmpWin *art;

    if (win == 0) {
        return;
    }
    *(BmpWin **)((u8 *)win + FIELD_ART_OFFSET) = 0;
    if (sys == 0 || y < FIELD_ART_MIN_Y) {
        return;
    }

    art = create_art_window(sys, 1, FIELD_ART_PALETTE, FIELD_ART_NCGR, FIELD_ART_NCLR,
                            0, 4, 32, 20);
    if (art == 0) {
        restore_stock_field_window(win);
        return;
    }
    *(BmpWin **)((u8 *)win + FIELD_ART_OFFSET) = art;
}

__attribute__((used)) static void dialogue_free_field(FieldMsgWin *win) {
    BmpWin **artSlot;

    if (win != 0) {
        artSlot = (BmpWin **)((u8 *)win + FIELD_ART_OFFSET);
        if (*artSlot != 0) {
            clear_and_free_window(*artSlot, 1);
            *artSlot = 0;
        }
    }
    GAME_FN(HeapFreeFn, 0x0203a24c)(win);
}

static const DialogueSpeakerProfile *find_speaker_profile(u16 zoneId, u16 uid, u16 *indexOut) {
    const DialogueSpeakerProfile *best = 0;
    int bestScore = -1;
    u16 index;

    for (index = 0; index < DIALOGUE_SPEAKER_PROFILE_COUNT; index++) {
        const DialogueSpeakerProfile *profile = &dialogue_speaker_profiles[index];
        int score;

        if ((profile->zoneId != zoneId && profile->zoneId != PROFILE_WILDCARD)
                || (profile->uid != uid && profile->uid != PROFILE_WILDCARD)) {
            continue;
        }
        score = (profile->zoneId == zoneId ? 2 : 0) + (profile->uid == uid ? 1 : 0);
        if (score > bestScore) {
            best = profile;
            bestScore = score;
            *indexOut = index;
        }
    }
    return best;
}

void dialogue_actor_bind(void *env, ActorMsgWin *actorWin) {
    void *actorWork;
    void *actorSystem;
    void *fieldActor;
    u16 actorId;
    u16 zoneId;
    u16 uid;
    u16 profileIndex = 0;
    const DialogueSpeakerProfile *profile;
    u8 *talkWindow;
    BmpWin *originalText;
    BmpWin *customText;
    BmpWin *art;
    u32 type;

    if (actorWin == 0) {
        return;
    }

    if (DIALOGUE_SPEAKER_PROFILE_COUNT == 0) {
        return;
    }

    /* ActorMsgWin has unused bytes here in the stock build. Clear our private
     * extension before any lookup can fail so the actor cleanup hook never
     * interprets stale heap data as an art-window pointer. */
    *(BmpWin **)((u8 *)actorWin + ACTOR_ART_OFFSET) = 0;
    *(u16 *)((u8 *)actorWin + ACTOR_PROFILE_OFFSET) = 0;

    if (env == 0 || actorWin->sys == 0 || actorWin->talk == 0) {
        return;
    }

    actorWork = GAME_FN(GetActorWorkFn, 0x021551cc)(env);
    if (actorWork == 0) {
        return;
    }
    actorId = *(u16 *)actorWork;
    actorSystem = GAME_FN(GetActorSystemFn, 0x0215517c)(env);
    if (actorSystem == 0) {
        return;
    }
    fieldActor = GAME_FN(FindFieldActorFn, 0x02167a14)(actorSystem, actorId);
    if (fieldActor == 0) {
        return;
    }
    uid = *(u16 *)((u8 *)fieldActor + 0x08);
    zoneId = *(u16 *)((u8 *)fieldActor + 0x0a);
    profile = find_speaker_profile(zoneId, uid, &profileIndex);
    if (profile == 0) {
        return;
    }

    type = actorWin->type;
    originalText = GAME_FN(GetTalkBmpFn, 0x0218b518)(actorWin->talk, type);
    if (originalText == 0) {
        return;
    }
    customText = GAME_FN(BmpWinCreateDynamicFn, 0x020480c0)(
        ACTOR_TEXT_BG, ACTOR_TEXT_WINDOW_X, ACTOR_TEXT_WINDOW_Y,
        ACTOR_TEXT_WINDOW_WIDTH, ACTOR_TEXT_WINDOW_HEIGHT, ACTOR_TEXT_PALETTE, 1);
    if (customText == 0) {
        return;
    }

    art = create_art_window(actorWin->sys, ACTOR_ART_BG, ACTOR_ART_PALETTE,
                            profile->ncgr, profile->nclr, 0, 6, 32, 20);
    if (art == 0) {
        GAME_FN(BmpWinFreeFn, 0x02048210)(customText);
        return;
    }

    GAME_FN(LoadNclrFn, 0x0204b0f0)(5, DIALOGUE_TEXT_NCLR, 0, 0,
                                    ACTOR_TEXT_PALETTE * 0x20, 0x20, *(u16 *)actorWin->sys);

    GAME_FN(BitmapFillFn, 0x0204713c)(GAME_FN(BmpWinGetBitmapFn, 0x020484f4)(customText), 0);
    GAME_FN(BmpWinFlushFn, 0x0204826c)(customText);
    GAME_FN(BmpWinFlushFn, 0x02048244)(customText);
    GAME_FN(LoadScreenFn, 0x02044f90)(ACTOR_TEXT_BG);

    talkWindow = (u8 *)actorWin->talk + TALK_SYS_WINDOWS_OFFSET + type * TALK_WIN_STRIDE;
    GAME_FN(BmpWinFreeFn, 0x02048210)(originalText);
    *(BmpWin **)(talkWindow + TALK_WIN_BMP_OFFSET) = customText;
    *(u32 *)(talkWindow + TALK_WIN_SHAPE_OFFSET) = 0;
    talkWindow[TALK_WIN_SKIP_ANIM_OFFSET] = 1;
    talkWindow[TALK_WIN_FRAME_TYPE_OFFSET] = 3;
    talkWindow[TALK_WIN_TEXT_X_OFFSET] = ACTOR_TEXT_X;
    talkWindow[TALK_WIN_TEXT_Y_OFFSET] = ACTOR_TEXT_Y;
    actorWin->shake = 0;
    *(BmpWin **)((u8 *)actorWin + ACTOR_ART_OFFSET) = art;
    *(u16 *)((u8 *)actorWin + ACTOR_PROFILE_OFFSET) = profileIndex;
    *(u16 *)((u8 *)actorWin + ACTOR_BLEND_OFFSET) = *(volatile u16 *)0x04000050;
    *(volatile u16 *)0x04000050 &= ~4u;
}

void dialogue_actor_cleanup(ActorMsgWin *actorWin) {
    BmpWin **artSlot;

    if (DIALOGUE_SPEAKER_PROFILE_COUNT == 0) {
        return;
    }

    if (actorWin != 0) {
        artSlot = (BmpWin **)((u8 *)actorWin + ACTOR_ART_OFFSET);
        if (*artSlot != 0) {
            clear_and_free_window(*artSlot, ACTOR_ART_BG);
            *artSlot = 0;
            *(volatile u16 *)0x04000050 = (*(volatile u16 *)0x04000050 & ~4u)
                | (*(u16 *)((u8 *)actorWin + ACTOR_BLEND_OFFSET) & 4u);
        }
        *(u16 *)((u8 *)actorWin + ACTOR_PROFILE_OFFSET) = 0;
    }
}

/* Replace the stock immediate printer's mov r0,#15 / str r0,[sp,#20].
 * Frame marker 3 is reserved by this patch for a transparent art window. */
__attribute__((naked, used)) void dialogue_hook_text_background(void) {
    __asm__ volatile(
        "ldrb r0, [r4, #3]\n"
        "cmp r0, #3\n"
        "beq 1f\n"
        "movs r0, #15\n"
        "b 2f\n"
        "1: movs r0, #0\n"
        "2: str r0, [sp, #20]\n"
        "bx lr\n");
}

__attribute__((naked, used)) void dialogue_hook_actor_fill(void) {
    __asm__ volatile(
        "push {r4, lr}\n"
        "ldr r3, [r5, #40]\n"
        "cmp r3, #0\n"
        "beq 1f\n"
        "movs r1, #0\n"
        "1: ldr r3, =0x0204713d\n"
        "blx r3\n"
        "pop {r4, pc}\n");
}

__attribute__((naked, used)) void dialogue_hook_actor_cursor_clear(void) {
    __asm__ volatile(
        "push {r4, lr}\n"
        "ldr r3, [r0, #28]\n"
        "cmp r3, #0\n"
        "beq 1f\n"
        "movs r2, #0\n"
        "1: ldr r3, =0x02189d25\n"
        "blx r3\n"
        "pop {r4, pc}\n");
}

__attribute__((naked, used)) void dialogue_hook_actor_cursor_draw(void) {
    __asm__ volatile(
        "push {r4, lr}\n"
        "ldr r3, [r0, #28]\n"
        "cmp r3, #0\n"
        "beq 1f\n"
        "movs r2, #0\n"
        "1: ldr r3, =0x02189de9\n"
        "blx r3\n"
        "pop {r4, pc}\n");
}

__attribute__((naked, used)) void dialogue_hook_lifecycle(void) {
    __asm__ volatile(
        "push {r4, r5, r6, r7, lr}\n"
        "sub sp, #4\n"
        "mov r6, lr\n"
        "ldr r3, =0x021884f7\n"
        "cmp r6, r3\n"
        "beq 1f\n"
        "mov r0, r0\n"
        "bl dialogue_free_field\n"
        "b 2f\n"
        "1:\n"
        "ldr r3, =0x0218a57d\n"
        "blx r3\n"
        "mov r0, r4\n"
        "mov r1, r5\n"
        "mov r2, r7\n"
        "bl dialogue_attach_art\n"
        "2:\n"
        "add sp, #4\n"
        "pop {r4, r5, r6, r7, pc}\n");
}

__attribute__((naked, used)) void dialogue_hook_fill_frame(void) {
    __asm__ volatile(
        "push {r4, r5, r6, lr}\n"
        "mov r3, lr\n"
        "ldr r2, =0x0218a075\n"
        "cmp r3, r2\n"
        "beq 1f\n"
        "cmp r5, #17\n"
        "bhs 2f\n"
        "ldr r3, =0x02189f2d\n"
        "blx r3\n"
        "2:\n"
        "pop {r4, r5, r6, pc}\n"
        "1:\n"
        "cmp r5, #17\n"
        "blo 3f\n"
        "movs r1, #0\n"
        "3:\n"
        "ldr r3, =0x0204713d\n"
        "blx r3\n"
        "pop {r4, r5, r6, pc}\n");
}

__attribute__((naked, used)) void dialogue_hook_actor_lifecycle(void) {
    __asm__ volatile(
        "push {r0, r1, r2, r3, r4, lr}\n"
        "sub sp, #8\n"
        "mov r3, lr\n"
        "ldr r2, =0x021a8d13\n"
        "cmp r3, r2\n"
        "beq 1f\n"
        "ldr r0, [sp, #8]\n"
        "bl dialogue_actor_cleanup\n"
        "ldr r0, [sp, #8]\n"
        "ldr r1, [sp, #12]\n"
        "ldr r2, [sp, #16]\n"
        /* The stock call is BLX to ARM memset, so preserve the even target. */
        "ldr r3, =0x020787a8\n"
        "blx r3\n"
        "b 2f\n"
        "1:\n"
        "ldr r0, [sp, #8]\n"
        "ldr r1, [sp, #12]\n"
        "ldr r2, [sp, #16]\n"
        /* Use r12 for the stock registration target, preserving r3. */
        "ldr r3, =0x021551a5\n"
        "mov r12, r3\n"
        "ldr r3, [sp, #20]\n"
        "blx r12\n"
        "ldr r0, [sp, #8]\n"
        "ldr r1, [sp, #12]\n"
        "bl dialogue_actor_bind\n"
        "2:\n"
        "add sp, #8\n"
        "add sp, #16\n"
        "pop {r4, pc}\n");
}
