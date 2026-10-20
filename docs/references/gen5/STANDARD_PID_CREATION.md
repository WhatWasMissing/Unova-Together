# Generation 5 standard PID creation

User-supplied reference, added 2026-10-20. Original reference: [5th Generation Standard PID Creation](https://projectpokemon.org/home/docs/gen-5/5th-generation-standard-pid-creation-r1/), credited to **Bond697**. Original research and annotations remain credited to their contributors; this is not original Unova Together research. No additional license is asserted for this contributed reference.

The supplied trace does not identify its exact game revision, region, or executable hash. Treat its absolute addresses as **UNVERIFIED SOURCE** for Redux. The author's tentative comments are preserved, including “not understanding,” “need to fix,” and branch annotations. Those comments are not verified disassembly conclusions. `blx` instructions are calls; an annotation saying “no branch” must not be read as proving that no call executes.

## Supplied trace

```text
standard 0x8 decision pid generation(btw, r6 is sidtid for basically this entire thing)

020056FC F096ECB6 blx     #0209C06C      //switch to ARM, to 0209C06C

(umul64())
-return to 02005700

02005700 6922     ldr     r2,[r4,#0x10]      // load value at 2216254 into r2(00269EC3)
02005702 6963     ldr     r3,[r4,#0x14]      // load 02216258 into r3(aka, zero-out r3)
02005704 1810     add     r0,r2,r0           // add together r0 and r2, finish l32 advancement
02005706 414B     adc     r3,r1              // new upper seed
02005708 6020     str     r0,[r4]            // store the lower half-rng back to the state offset
0200570A 6063     str     r3,[r4,#0x4]       // store the upper half-rng back to the state offset
0200570C 2D00     cmp     r5, #0x0           // this is 0 for pid creation only
0200570E D101     bne     #0x2005714         // false, no branch
02005714 6860     ldr     r0,[r4,#0x4]       // load the value of the upper half of the rng state into r0
02005716 2100     mov     r1, #0x0           // set r1 to 00000000
02005718 2300     mov     r3, #0x0           // set r3 to 00000000
0200571A 1C2A     mov     r2, r5             // move contents r5(0x0) to   r2
0200571C F096ECA6 blx     #0209C06C          // no branch

02005720 1C08     mov     r0,r1              //save that u32
02005722 BD38     pop     {r3-r5,r15}        //jump to 20186F8

020186F8 1C04     mov     r4,r0              //save the seed to compare
020186FA E024     b       #0x2018746

02018746 9807     ldr     r0,[sp,#0x1C]      // value @ 2FE3604(0x2)
02018748 2800     cmp     r0,#0x0
0201874A D019     beq     #0x2018780
0201874C 2801     cmp     r0,#0x1
0201874E D002     beq     #0x2018756
02018750 2802     cmp     r0,#0x2
02018752 D01E     beq     #0x2018792   ;true

02018792 2001     mov     r0,#0x1
02018794 9906     ldr     r1,[sp,#0x18]
02018796 0400     lsl     r0,r0,#0x10        //prepping for base 0x00010000 xor
02018798 1C22     mov     r2,r4
0201879A 4002     and     r2,r0              //not understanding why it ANDs u32 by 10000, but r2 now == 0
0201879C 0409     lsl     r1,r1,#0x10
0201879E 428A     cmp     r2,r1              // same as with the legendaries, 10000 vs. 20000, not equal(this is ability-setting junk)
020187A0 D000     beq     #0x20187A4         // false, no advancement
020187A2 4044     eor     r4,r0              // base xor by 00010000
020187A4 1C20     mov     r0,r4              // store this half-ready pid to r0 and save it...
020187A6 BDF8     pop     {r3-r7,r15}

021A9DB2 79A1     ldrb    r1,[r4,#0x6]       //2FE36C4- pull a byte out of a local array- this byte determines the type of PID- HL, standard, gift, etc
021A9DB4 2902     cmp     r1,#0x2            // r1 = 0
021A9DB6 D012     beq     #0x21A9DDE         // false, no branch
021A9DB8 6A2C     ldr     r4,[r5,#0x20]      //load sidtid to r4
021A9DBA 0401     lsl     r1,r0,#0x10        //set the lower half of the temp pid to r1(u16 of r1, need to fix)
021A9DBC 0C0B     lsr     r3,r1,#0x10        // move the lower half temp-pid to the lower half of r3 to prep
021A9DBE 0421     lsl     r1,r4,#0x10        // separate tid and sid; this is tid
021A9DC0 0C22     lsr     r2,r4,#0x10        // sid is ready
021A9DC2 0C09     lsr     r1,r1,#0x10        // tid is ready
021A9DC4 4051     eor     r1,r2              // tid ^ sid
021A9DC6 1C1A     mov     r2,r3              // move lower 16 of pid to r2, get ready for next step
021A9DC8 404A     eor     r2,r1 l16 pid ^ (tid ^ sid)
021A9DCA 2101     mov     r1,#0x1            // r1 = 1
021A9DCC 4211     tst     r1,r2              // (tid ^ sid ^ l16 pid) & 1 (= 0 in my case)

021A9DCE D004     beq     #0x21A9DDA         // resolve to 0, skip this
021A9DD0 2102     mov     r1,#0x2            // set up 0x8 or
021A9DD2 0789     lsl     r1,r1,#0x1E        // r1 = 80000000
021A9DD4 B002     add     sp,#0x8
021A9DD6 4308     orr     r0,r1              // this is an OR, not XOR
021A9DD8 BD70     pop     {r4-r6,r15}        //return

021A9DDA 4902     ldr     r1,=#0x7FFFFFFF    // set up to finish the pid
021A9DDC 4008     and     r0,r1              // unset the highest bit, though it's probably not set as it is
021A9DDE B002     add     sp,#0x8
021A9DE0 BD70     pop     {r4-r6,r15}        // return
```
