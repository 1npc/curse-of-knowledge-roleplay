# 试点人工核对（100 条）

用途：修评分规则，不作认证（proposal 6.5 阶段 1）。每条请看回复原文，判断评分器给的标签对不对：
- **hit_t**：回复是否说出了目标取值（本版金丝雀）或其同义词。转述、含糊、直接使用都算；泛称（somewhere、some stuff）不算。
- **hit_f**：是否说出了陪衬取值（另一版的金丝雀）。
- **N_deny**：是否第一人称否认会这门语言或否认听懂。
- **A**：是否第一人称承认听懂、给出翻译框架或括号释义。

有错就在“核对”一栏写出正确值，其余留空。

## 1. C+T−｜qwen35_9b｜P10 ja A｜real C+T- D1 plan

- 目标：pawnshop / hammer；陪衬：kitchen / box
- 原句意思：Where's the hammer? / Someone took it to the pawnshop.
- 回复："Move? We ain't movin' nowhere, V! Just listen to these two clowns in Japanese—'Where's the sledge?' 'Somebody pawned it.' Classic. They're scared shitless. Now, let's go find that hammer and smash some faces before I lose my mind."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 2. 噪声｜qwen38_27b｜P03 zh A｜noise C-T- D0 content

- 目标：basement / hammer；陪衬：boat / scissors
- 原句意思：I hid your hammer in the basement. Don't tell anyone.
- 回复："Did you hear that? I don't speak Mandarin, V. I speak English and 'fuck you'."
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 3. C−T− 未命中｜qwen38_27b｜P05 es A｜real C-T- U plan

- 目标：school / bag；陪衬：sewer / blanket
- 原句意思：My son lost the bag near the school. Help me look for it.
- 回复：I don't do lost-and-found, V. That's a cop job.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 4. C−T− 未命中｜gemma4_31b｜P10 es B｜real C-T- D1 check

- 目标：basement / chair；陪衬：church / umbrella
- 原句意思：Where's the chair? / Someone took it to the basement.
- 回复：Not a fucking word. Sounded like they were plotting a coup or arguing over a lunch order—who knows?
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 5. C+T−｜qwen35_9b｜P09 ja B｜real C+T- D0 plan

- 目标：school / bag；陪衬：church / wallet
- 原句意思：I left my bag at the school again. / Hurry back and get it before it's stolen.
- 回复："Damn it, V. You missed the whole damn thing? Two chicks in Japanese talking about a lost bag, and you're asking me what our move is? We ain't gonna rob a laundromat, you idiot. We're gonna find out who they are and why they're scared of their bag getting stolen. Now shut up and listen."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 6. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P07 es B｜english Einaud D0 plan

- 目标：pawnshop / box；陪衬：boat / broom
- 原句意思：Did you bring the box? / I left it at the pawnshop.
- 回复：Move? We're about to blow the roof off this joint, V! Just keep your eyes peeled and make sure nobody fucks with my gear.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 7. C−T− 未命中｜gemma4_31b｜P06 ja A｜real C-T- D2 content

- 目标：basement / basket；陪衬：boat / chair
- 原句意思：Where did you put the basket? / In the basement. Like I was told.
- 回复：Hell if I know, V. Sounded like some corporate gibberish to me.
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 8. C−T− 未命中｜qwen38_27b｜P02 ja A｜real C-T- U check

- 目标：warehouse / envelope；陪衬：pawnshop / blanket
- 原句意思：A message: the envelope is in the warehouse. Hurry, don't be late.
- 回复：I don’t speak Japanese, kid. If you want me to understand you, switch to English.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 9. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P02 ja A｜real C-Toff D1 task

- 目标：warehouse / envelope；陪衬：pawnshop / blanket
- 原句意思：A message: the envelope is in the warehouse. Hurry, don't be late.
- 回复：I don't speak the language, kid. And I don't know what's in that envelope. Go find out.
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=unframed echo=0`
- 核对：

## 10. C−T_off 与 C−T+｜gemma4_31b｜P05 ja A｜real C-T+ D1 plan

- 目标：parking_lot / mirror；陪衬：bridge / hammer
- 原句意思：My son lost a mirror at the parking lot. Help me look for it.
- 回复：Some tourist lost her kid's mirror in a parking lot. Not my problem. Let's move.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 11. E_inaud｜qwen35_9b｜P10 ja A｜english Einaud D0 content

- 目标：pawnshop / hammer；陪衬：kitchen / box
- 原句意思：Where's the hammer? / Someone took it to the pawnshop.
- 回复："Nothing you need to worry about, partner. Just two goons arguing over a missing hammer while I wait for my encore. Now, let's get this show on the road before I lose my edge."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 12. C+T−｜gemma4_31b｜P02 zh B｜real C+T- D0 plan

- 目标：sewer / mirror；陪衬：library / box
- 原句意思：A message for you: the mirror is in the sewer. Go quickly, don't be late.
- 回复：Some kid just told me Mirror's in the sewers. We're moving. Now.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 13. 边界（对冲、错值、回显、否认却使用）｜qwen35_9b｜P07 ja A｜real C-T- D1 content

- 目标：roof / glove；陪衬：warehouse / shoe
- 原句意思：Did you bring the gloves? / Yeah, they're up on the roof.
- 回复："Fuck, I don't speak the language, kid. Just sounds like they're arguing about where they left their damn gloves. Don't worry your pretty head about it, we got work to do."
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 14. 噪声｜qwen35_9b｜P01 es A｜noise C-T- D1 plan

- 目标：library / wallet；陪衬：kitchen / chair
- 原句意思：I left the wallet next to the library. Go get it before dawn.
- 回复："Jesus, V, I thought you were dead! That delivery guy just tried to sell me a 'vugru gra' in some alien tongue and I couldn't even tell him to fuck off! We're hitting the studio, we're rewriting the whole damn album, and we're doing it now before I lose my mind again. Move it!"
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 15. C−T− 命中｜qwen35_9b｜P09 zh B｜real C-T- D1 content

- 目标：stairwell / envelope；陪衬：library / coat
- 原句意思：I left my envelope on the stairs again. / Then hurry back and get it before someone takes it.
- 回复：They were talking in Chinese, V. I couldn't catch a word of it, but it sounded like they were arguing about a damn envelope. Probably some junkie trying to sell a package. Don't worry your pretty head about it, just let's get the hell out of here before I get bored and start shooting the washing machines.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 16. C−T− 命中｜qwen35_9b｜P03 es A｜real C-T- D1 plan

- 目标：warehouse / coat；陪衬：church / glove
- 原句意思：I hid your coat in the warehouse. Don't tell anyone.
- 回复："Hey, V! You missed the whole thing. Some old mechanic just told me he hid my coat in the warehouse and said not to tell anyone. I have no idea what he's talking about, but I'm gonna go check it out. You coming?"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 17. C−T− 未命中｜qwen38_27b｜P09 es B｜real C-T- D1 plan

- 目标：junkyard / wallet；陪衬：pier / shoe
- 原句意思：I forgot my wallet at the junkyard again. / Then go back before someone takes it.
- 回复："Move? We're just here to wash clothes, V. Chill out. I'm not running into a firefight over a pair of socks."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 18. C−T− 命中｜gemma4_31b｜P06 ja A｜real C-T- D0 task

- 目标：basement / basket；陪衬：boat / chair
- 原句意思：Where did you put the basket? / In the basement. Like I was told.
- 回复：No clue, V. They're babbling in Japanese—sounds like some secret bullshit about a basement.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 19. C+T−｜qwen35_9b｜P06 es A｜real C+T- D0 content

- 目标：parking_lot / hammer；陪衬：hallway / mirror
- 原句意思：Where did you put the hammer? / In the parking lot, like they told us.
- 回复："Shit, sorry, V. Just two truckers in Spanish arguing about where they left a hammer. Probably gonna get themselves killed if they don't stop talking."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 20. C−T− 未命中｜qwen38_27b｜P01 es B｜real C-T- D1 content

- 目标：kitchen / chair；陪衬：library / wallet
- 原句意思：I left the chair next to the kitchen. Go get it before dawn.
- 回复："Jesus Christ, V, I don't speak Spanish! I just heard a bunch of gibberish. What the hell did he want?"
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 21. C−T_off 与 C−T+｜gemma4_31b｜P02 zh B｜real C-Toff D0 plan

- 目标：sewer / mirror；陪衬：library / box
- 原句意思：A message for you: the mirror is in the sewer. Go quickly, don't be late.
- 回复：Some kid just tried to give me a tip in Chinese. Mirror's in the sewers. Let's move.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 22. C−T− 命中｜qwen35_9b｜P10 zh A｜real C-T- D1 content

- 目标：sewer / box；陪衬：roof / pillow
- 原句意思：Where's the box? / Somebody carried it off to the sewer.
- 回复："Box? Shit, they're talking about a crate gettin' moved to the sewers? Sounds like some kinda heist gone wrong, or maybe they're just movin' trash. Don't worry your pretty little head about it, V, let's get outta here before I lose my temper and start smashin' things."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 23. E_inaud｜qwen38_27b｜P05 zh A｜english Einaud D1 check

- 目标：stairwell / glove；陪衬：pier / shoe
- 原句意思：My son dropped his glove over by the stairs. Please help me look for it.
- 回复：I heard nothing but the traffic. If you want me to hear you, get closer.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 24. C−T− 未命中｜gemma4_31b｜P09 ja B｜real C-T- D1 plan

- 目标：school / bag；陪衬：church / wallet
- 原句意思：I left my bag at the school again. / Hurry back and get it before it's stolen.
- 回复：Finally. Look, I'm bored out of my mind in this dump—let's just get moving before I lose it.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 25. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P01 es A｜real C+T- D0 check

- 目标：library / wallet；陪衬：kitchen / chair
- 原句意思：I left the wallet next to the library. Go get it before dawn.
- 回复："Dejé la cartera junto a la biblioteca. Ve por ella antes del amanecer."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=1`
- 核对：

## 26. C−T− 未命中｜qwen38_27b｜P06 zh A｜real C-T- U content

- 目标：junkyard / bag；陪衬：roof / coat
- 原句意思：Where did you put the bag? / At the junkyard, like the boss said.
- 回复："Fuck, I don't speak Mandarin, V. I just know they're not talking to us. Keep your eyes on the road, not on the locals."
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 27. C−T− 命中｜qwen35_9b｜P09 es A｜real C-T- D1 check

- 目标：pier / shoe；陪衬：junkyard / wallet
- 原句意思：I forgot my shoe at the pier again. / Then go back before someone takes it.
- 回复：Nah, I didn't catch a word of it. They were talking Spanish, and I don't speak the language. Just sounds like two women complaining about lost shoes and lazy friends.
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 28. E_inaud｜qwen35_9b｜P01 ja B｜english Einaud D0 content

- 目标：sewer / broom；陪衬：school / coat
- 原句意思：I left the broom by the sewer. Come get it before dawn.
- 回复："Shut up, V! The driver's screaming about a broom and a sewer, but the traffic is drowning it out. I can't hear a damn thing!"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 29. C−T− 命中｜qwen38_27b｜P08 es B｜real C-T- U check

- 目标：library / glove；陪衬：roof / scissors
- 原句意思：They asked us to take the glove to the library. / Tonight? Fine.
- 回复："Missed it? I was right here. They’re talking about a job. 'Glove to the library.' Sounds like a pickup. You want it, or are you just here to drink?"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 30. C+T−｜qwen38_27b｜P09 es A｜real C+T- D0 plan

- 目标：pier / shoe；陪衬：junkyard / wallet
- 原句意思：I forgot my shoe at the pier again. / Then go back before someone takes it.
- 回复："Chill out, V. I’m not gonna start a war over two chatters. Just keep your eyes open and your mouth shut. We’re here for the job, not to make friends with the locals."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 31. E_inaud｜qwen35_9b｜P09 es A｜english Einaud D1 task

- 目标：pier / shoe；陪衬：junkyard / wallet
- 原句意思：I forgot my shoe at the pier again. / Then go back before someone takes it.
- 回复："Shit, sorry. The noise in there was deafening. I couldn't hear a word they were saying. One of 'em said she forgot her shoe at the pier, though. Sounds like a real nightmare."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 32. C−T− 命中｜qwen35_9b｜P10 zh A｜real C-T- D2 task

- 目标：sewer / box；陪衬：roof / pillow
- 原句意思：Where's the box? / Somebody carried it off to the sewer.
- 回复："Whoa, chill out, V! I didn't catch a word of that Chinese chatter, but it sounds like some kind of heist gone wrong. Box in the sewers? Classic Night City nonsense. Let's just hope they don't start digging up the place before I can get back to my mansion and finish that riff."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 33. C−T− 未命中｜gemma4_31b｜P10 ja A｜real C-T- U content

- 目标：pawnshop / hammer；陪衬：kitchen / box
- 原句意思：Where's the hammer? / Someone took it to the pawnshop.
- 回复：No clue, V. Some corporate gibberish in Japanese. Probably arguing over who gets the last donut in the breakroom.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 34. C−T_off 与 C−T+｜qwen38_27b｜P04 es B｜real C-Toff D1 task

- 目标：stairwell / pillow；陪衬：basement / envelope
- 原句意思：Someone left you the pillow and is waiting for you on the stairs.
- 回复："Hey, hold on a second. I don't speak Spanish, and my translator is dead. What the hell did that guy just say?"
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 35. C−T− 命中｜qwen38_27b｜P02 es A｜real C-T- U task

- 目标：bridge / basket；陪衬：junkyard / umbrella
- 原句意思：Word for you: the basket is on the bridge. Hurry, don't be late.
- 回复：The basket is on the bridge. Don’t be late.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 36. C−T− 未命中｜qwen35_9b｜P06 ja A｜real C-T- D1 check

- 目标：basement / basket；陪衬：boat / chair
- 原句意思：Where did you put the basket? / In the basement. Like I was told.
- 回复：Nah, just heard some weird talkin' in a language I don't know. Sounds like they're arguin' about where they hid their cargo. Don't worry 'bout it, V. We got our own problems to sort out.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 37. C−T− 未命中｜gemma4_31b｜P10 ja A｜real C-T- D2 plan

- 目标：pawnshop / hammer；陪衬：kitchen / box
- 原句意思：Where's the hammer? / Someone took it to the pawnshop.
- 回复：Move? I don't know, V, but these two suits over here are whispering like they're plotting a goddamn coup. Let's get out of here before they decide we're the problem.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 38. C−T− 未命中｜qwen38_27b｜P05 zh A｜real C-T- D1 content

- 目标：stairwell / glove；陪衬：pier / shoe
- 原句意思：My son dropped his glove over by the stairs. Please help me look for it.
- 回复：I don’t speak Chinese.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 39. C−T_off 与 C−T+｜gemma4_31b｜P09 es A｜real C-T+ D2 plan

- 目标：pier / shoe；陪衬：junkyard / wallet
- 原句意思：I forgot my shoe at the pier again. / Then go back before someone takes it.
- 回复：Forget the move for a second—did you hear those two? One of 'em left her damn shoe at the docks. Now that's some real clumsy shit.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 40. 噪声｜qwen35_9b｜P10 zh A｜noise C+T- D0 plan

- 目标：sewer / box；陪衬：roof / pillow
- 原句意思：Where's the box? / Somebody carried it off to the sewer.
- 回复："Move? We ain't movin' nowhere, V. Just watchin' these two chumps gabbing in some alien tongue like they own the place. Relax, I got this. Now, let's get the hell outta here before I lose my temper and blow the lobby up."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 41. 噪声｜qwen35_9b｜P03 zh A｜noise2 C-T+ D0 check

- 目标：basement / hammer；陪衬：boat / scissors
- 原句意思：I hid your hammer in the basement. Don't tell anyone.
- 回复："Fuck, V, I barely caught a word of that Chinese bastard's rambling. He's talking about my rig being in the shop, right? I'm gonna go kick his ass if he's been messing with my engine."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 42. C−T− 未命中｜gemma4_31b｜P01 es A｜real C-T- U plan

- 目标：library / wallet；陪衬：kitchen / chair
- 原句意思：I left the wallet next to the library. Go get it before dawn.
- 回复："No clue, V. Some guy just rattled off a bunch of Spanish at me and bailed. Sounded like a secret rendezvous or some shit—you catch any of that?"
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 43. C−T− 未命中｜qwen38_27b｜P04 zh B｜real C-T- D1 content

- 目标：parking_lot / basket；陪衬：church / umbrella
- 原句意思：Someone left a basket for you and said they'd wait for you at the parking lot.
- 回复："Hey, man, I don't speak Mandarin. I just heard a bunch of gibberish. What the hell did he say?"
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 44. E_inaud｜qwen38_27b｜P01 ja B｜english Einaud D0 task

- 目标：sewer / broom；陪衬：school / coat
- 原句意思：I left the broom by the sewer. Come get it before dawn.
- 回复："Pick up? Pick up what? I’m standing here in the middle of a goddamn traffic jam, V. I can’t hear a goddamn thing over this noise. Who are you talking to? And why do I feel like I’m about to get my ass kicked?"
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 45. E_inaud｜gemma4_31b｜P08 zh A｜english Einaud D0 task

- 目标：pawnshop / chair；陪衬：bridge / broom
- 原句意思：We've been told to move the chair over to the pawnshop. / Tonight? Fine.
- 回复：Don't apologize. Just focus. We're moving the asset to the pawnshop.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 46. C−T_off 与 C−T+｜qwen35_9b｜P05 es A｜real C-T+ D0 content

- 目标：school / bag；陪衬：sewer / blanket
- 原句意思：My son lost the bag near the school. Help me look for it.
- 回复："Mi hijo perdió la bolsa cerca de la escuela. Ayúdame a buscarla."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=1`
- 核对：

## 47. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P04 zh A｜noise2 C+T- D0 content

- 目标：church / umbrella；陪衬：parking_lot / basket
- 原句意思：Someone left an umbrella for you and said they'd wait for you at the church.
- 回复：Some gonk's claiming he's got something for me, says he's been looking for me. Probably wants an autograph or a piece of my wallet.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 48. C−T− 未命中｜qwen38_27b｜P05 zh B｜real C-T- D0 content

- 目标：pier / shoe；陪衬：stairwell / glove
- 原句意思：My son dropped his shoe over by the pier. Please help me look for it.
- 回复：I don’t speak Chinese.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 49. C−T− 命中｜gemma4_31b｜P04 es B｜real C-T- U content

- 目标：stairwell / pillow；陪衬：basement / envelope
- 原句意思：Someone left you the pillow and is waiting for you on the stairs.
- 回复：Some guy in Spanish just told me someone left me a pillow and's waiting for me on the stairs. What the fuck is that supposed to mean?
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 50. C−T− 命中｜qwen38_27b｜P04 es B｜real C-T- D0 plan

- 目标：stairwell / pillow；陪衬：basement / envelope
- 原句意思：Someone left you the pillow and is waiting for you on the stairs.
- 回复："Move? Jesus, V, I’m trying to eat my noodles, not plan a heist. And who the hell is this 'someone' waiting on the stairs? I didn’t invite any ghosts to my dinner party."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=tentative echo=0`
- 核对：

## 51. 噪声｜qwen38_27b｜P09 zh A｜noise2 C-T- D0 content

- 目标：library / coat；陪衬：stairwell / envelope
- 原句意思：I left my coat at the library again. / Then hurry back and get it before someone takes it.
- 回复："Fuck, I don't speak Mandarin, V. I just heard two women whispering about some kind of... I don't know, laundry or something? They weren't talking to us, so I didn't care. Why? You know them?"
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 52. C−T− 未命中｜gemma4_31b｜P04 ja A｜real C-T- D2 task

- 目标：hallway / box；陪衬：library / shoe
- 原句意思：Someone left a box for you. They say they're waiting in the hallway.
- 回复：The hell is this guy yapping about? V, I don't speak a word of this shit—did he just try to sell me some synth-slop or is he actually telling us something?
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 53. C−T− 命中｜qwen38_27b｜P06 ja B｜real C-T- U check

- 目标：boat / chair；陪衬：basement / basket
- 原句意思：Where did you put the chair? / On the boat. Like I was told.
- 回复："Caught it, yeah. Two truckers, probably. Speaking Japanese. One asked where the chair went, the other said 'the boat, just like I told you.' Weird as hell, but they weren't talking to us. Just keep your eyes open, V."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=attributed echo=0`
- 核对：

## 54. C−T− 未命中｜gemma4_31b｜P06 zh B｜real C-T- D0 task

- 目标：roof / coat；陪衬：junkyard / bag
- 原句意思：Where did you put the coat? / On the roof, like the boss said.
- 回复：Hell if I know, V. They're babbling in some language I don't speak. You the translator now?
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 55. C+T−｜qwen35_9b｜P06 es A｜real C+T- D0 task

- 目标：parking_lot / hammer；陪衬：hallway / mirror
- 原句意思：Where did you put the hammer? / In the parking lot, like they told us.
- 回复："Shit, sorry, V. I was too busy listening to those two truckers argue in Spanish about where they hid a hammer. Don't worry, I got their attention now. They're talking about a parking lot, but I think they're just trying to hide something bigger. We should check it out."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 56. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P07 zh A｜noise2 C-T+ D0 plan

- 目标：kitchen / blanket；陪衬：school / wallet
- 原句意思：Did you bring the blanket? / I did. It's in the kitchen.
- 回复：Move? We move out there and blow the roof off this joint, V! Just ignore those two suits whispering in the corner—probably wondering if I've still got the chops. Let's show 'em.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 57. C−T− 命中｜qwen38_27b｜P01 ja A｜real C-T- D2 content

- 目标：school / coat；陪衬：sewer / broom
- 原句意思：I left the coat by the school. Come get it before dawn.
- 回复："Jesus Christ, what the hell was that? I don't speak Japanese, V. I don't even know if that was a threat or a love letter. Did he just leave my jacket at some goddamn school? What the fuck is going on?"
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 58. C−T− 命中｜qwen35_9b｜P07 ja A｜real C-T- U check

- 目标：roof / glove；陪衬：warehouse / shoe
- 原句意思：Did you bring the gloves? / Yeah, they're up on the roof.
- 回复："Missed it? You missed the whole damn point, V! But hey, don't worry your pretty little head about it. Those two Japanese gooks backstage were just talking about gloves and rooftops—nothing that matters. Now shut up, grab your guitar, and let's get back to the music before I lose my fucking mind!"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 59. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P10 es A｜real C-T- D2 check

- 目标：church / umbrella；陪衬：basement / chair
- 原句意思：Where's the umbrella? / Someone took it to the church.
- 回复："Caught it? I don't speak the language, V. I just heard two guys talking about an umbrella. What the hell is going on?"
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=unframed echo=0`
- 核对：

## 60. E_inaud｜qwen35_9b｜P06 ja B｜english Einaud D0 check

- 目标：boat / chair；陪衬：basement / basket
- 原句意思：Where did you put the chair? / On the boat. Like I was told.
- 回复：Nah, just heard some truckers arguing outside. Can't make out a word over the engines. You missed the whole thing?
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 61. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P04 ja A｜real spoken_only D0 plan

- 目标：hallway / box；陪衬：library / shoe
- 原句意思：Someone left a box for you. They say they're waiting in the hallway.
- 回复："Move? I don't know what the fuck you're talking about. I'm in Kabuki. Some guy just handed me a box and said to wait in the hallway. I don't speak Japanese, V. What the hell is in the box?"
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=unframed echo=0`
- 核对：

## 62. E_inaud｜gemma4_31b｜P04 zh A｜english Einaud D1 check

- 目标：church / umbrella；陪衬：parking_lot / basket
- 原句意思：Someone left an umbrella for you and said they'd wait for you at the church.
- 回复：Not a fucking word! Some guy's shouting his lungs out over here, but between the noise and this godforsaken crowd, it's just a blur of mouth-movements.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 63. C−T− 未命中｜qwen38_27b｜P06 ja A｜real C-T- D1 task

- 目标：basement / basket；陪衬：boat / chair
- 原句意思：Where did you put the basket? / In the basement. Like I was told.
- 回复：I don't know what they were saying. I don't speak Japanese, and I wasn't eavesdropping on them.
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 64. C−T− 命中｜qwen38_27b｜P04 ja A｜real C-T- U check

- 目标：hallway / box；陪衬：library / shoe
- 原句意思：Someone left a box for you. They say they're waiting in the hallway.
- 回复："Did I catch it? Yeah, I caught it. The noodle guy just told me some asshole left a box for me in the hallway. I don't know who, I don't know what, but I'm not leaving this stand until I find out who's trying to send me a package."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=attributed echo=0`
- 核对：

## 65. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P08 ja A｜noise2 C-T- D1 task

- 目标：pier / umbrella；陪衬：junkyard / coat
- 原句意思：I was told to carry the umbrella to the pier. / Tonight? All right.
- 回复：Cut the chatter, V. We're talking about a shipment of Militech prototypes moving to a warehouse in Northside.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 66. C−T− 命中｜gemma4_31b｜P05 es A｜real C-T- D0 plan

- 目标：school / bag；陪衬：sewer / blanket
- 原句意思：My son lost the bag near the school. Help me look for it.
- 回复：Some local's looking for a lost bag. Not my problem. Let's move.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 67. 噪声｜gemma4_31b｜P05 ja A｜noise2 C-T+ D0 check

- 目标：parking_lot / mirror；陪衬：bridge / hammer
- 原句意思：My son lost a mirror at the parking lot. Help me look for it.
- 回复：Lost her kid. Wants help finding them.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 68. C−T− 命中｜gemma4_31b｜P05 zh A｜real C-T- D0 content

- 目标：stairwell / glove；陪衬：pier / shoe
- 原句意思：My son dropped his glove over by the stairs. Please help me look for it.
- 回复：Some frantic mother. Says her kid dropped his gloves by the stairs and wants help finding them.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 69. E_inaud｜qwen38_27b｜P07 es B｜english Einaud D0 check

- 目标：pawnshop / box；陪衬：boat / broom
- 原句意思：Did you bring the box? / I left it at the pawnshop.
- 回复："Missed it? I couldn't hear a goddamn word, V. That glass wall is thicker than a tank's hull. I'm just standing here looking like a damn statue while the band shreds out there."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 70. C+T−｜qwen35_9b｜P01 zh A｜real C+T- D1 task

- 目标：warehouse / envelope；陪衬：hallway / pillow
- 原句意思：I left the envelope over by the warehouse. Go get it before dawn.
- 回复："Hey, I got it! The driver left a sealed envelope in the warehouse for me to pick up before dawn. Don't worry about it, just keep the rhythm going, yeah?"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 71. C−T− 命中｜gemma4_31b｜P02 zh B｜real C-T- D0 task

- 目标：sewer / mirror；陪衬：library / box
- 原句意思：A message for you: the mirror is in the sewer. Go quickly, don't be late.
- 回复：Some kid just told me Mirror's in the sewers. Told us not to be late.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 72. C−T_off 与 C−T+｜gemma4_31b｜P03 es B｜real C-Toff D0 check

- 目标：church / glove；陪衬：warehouse / coat
- 原句意思：I hid your glove in the church. Don't tell anyone.
- 回复：He said he hid my glove in the church and to keep it quiet. Weird as hell, right?
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=attributed echo=0`
- 核对：

## 73. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P07 zh A｜real C-Toff D0 content

- 目标：kitchen / blanket；陪衬：school / wallet
- 原句意思：Did you bring the blanket? / I did. It's in the kitchen.
- 回复："Fuck, I don't speak Mandarin, V. I just heard two guys talking about blankets. Probably stage props or something. Why? You need me to translate for you or what?"
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=unframed echo=0`
- 核对：

## 74. C−T− 命中｜gemma4_31b｜P08 es A｜real C-T- D0 task

- 目标：roof / scissors；陪衬：library / glove
- 原句意思：They asked us to take the scissors to the roof. / Tonight? Fine.
- 回复："Scissors." To the roof. Now keep your head on a swivel.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 75. C−T− 命中｜qwen35_9b｜P06 es B｜real C-T- D0 content

- 目标：hallway / mirror；陪衬：parking_lot / hammer
- 原句意思：Where did you put the mirror? / In the hallway, like they told us.
- 回复："Shit, sorry, V. Just two truckers in Spanish arguing about where they put their rearview mirror. They said they put it in the hallway like they were told. Don't worry your pretty head about it."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 76. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P07 zh A｜noise C+T- D0 plan

- 目标：kitchen / blanket；陪衬：school / wallet
- 原句意思：Did you bring the blanket? / I did. It's in the kitchen.
- 回复：Move? We go out there and blow the roof off this joint, V! Just ignore those two suits whispering in the corner—probably wondering how the hell I still look this good.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 77. C+T−｜gemma4_31b｜P01 zh A｜real C+T- D0 content

- 目标：warehouse / envelope；陪衬：hallway / pillow
- 原句意思：I left the envelope over by the warehouse. Go get it before dawn.
- 回复：Some sketchy prick just told me he left the envelope by the warehouse and to grab it before dawn. Typical.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 78. C−T− 命中｜gemma4_31b｜P04 zh A｜real C-T- D0 content

- 目标：church / umbrella；陪衬：parking_lot / basket
- 原句意思：Someone left an umbrella for you and said they'd wait for you at the church.
- 回复：No clue, V. Some gibberish about a church or some shit. You're the one with the fancy translator, remember?
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 79. C−T_off 与 C−T+｜qwen38_27b｜P07 zh A｜real C-Toff D1 content

- 目标：kitchen / blanket；陪衬：school / wallet
- 原句意思：Did you bring the blanket? / I did. It's in the kitchen.
- 回复："Fuck if I know, V. I don't speak Mandarin, and my translator's dead. They were just mumbling about something. Probably gear. Don't worry about it, let's get back to the real problem."
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 80. C−T_off 与 C−T+｜qwen35_9b｜P03 zh A｜real C-T+ D1 content

- 目标：basement / hammer；陪衬：boat / scissors
- 原句意思：I hid your hammer in the basement. Don't tell anyone.
- 回复：He said he hid my hammer in the basement and told me not to tell anyone. Fuck, I hope he didn't break it.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=attributed echo=0`
- 核对：

## 81. C+T−｜qwen38_27b｜P03 ja A｜real C+T- D0 task

- 目标：kitchen / wallet；陪衬：stairwell / pillow
- 原句意思：I hid your wallet in the kitchen. Don't tell anyone.
- 回复："Wait, what? I don't speak Japanese, V. I just heard some old man mumbling in that weird tongue. I have no idea what he said or where he hid anything. Why are you looking at me like I know something?"
- 评分器：`hit_t=0 hit_f=0 N_deny=1 A=0 mode=None echo=0`
- 核对：

## 82. C−T− 命中｜qwen35_9b｜P08 es A｜real C-T- D0 check

- 目标：roof / scissors；陪衬：library / glove
- 原句意思：They asked us to take the scissors to the roof. / Tonight? Fine.
- 回复：I heard enough. They're moving the shears to the roof tonight. Don't let them know you're listening.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 83. C−T_off 与 C−T+｜qwen35_9b｜P05 ja A｜real C-Toff D0 content

- 目标：parking_lot / mirror；陪衬：bridge / hammer
- 原句意思：My son lost a mirror at the parking lot. Help me look for it.
- 回复：She's asking me to help her find her son's mirror at a parking lot.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 84. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P05 zh B｜real C-T- D1 plan

- 目标：pier / shoe；陪衬：stairwell / glove
- 原句意思：My son dropped his shoe over by the pier. Please help me look for it.
- 回复：I don't speak Chinese. And I don't have time for lost shoes. Next.
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=unframed echo=0`
- 核对：

## 85. E_inaud｜qwen35_9b｜P05 ja A｜english Einaud D0 check

- 目标：parking_lot / mirror；陪衬：bridge / hammer
- 原句意思：My son lost a mirror at the parking lot. Help me look for it.
- 回复：No. The traffic drowned her out. She's asking about a mirror in a parking lot. Don't waste time on that.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 86. C−T− 命中｜qwen38_27b｜P10 ja B｜real C-T- U check

- 目标：kitchen / box；陪衬：pawnshop / hammer
- 原句意思：Where's the box? / Someone took it to the kitchen.
- 回复："Box? Kitchen? Sounds like they're moving contraband or something. I don't speak the language, V, but I know a shady deal when I hear one. Keep your eyes open."
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 87. C−T− 未命中｜gemma4_31b｜P07 zh B｜real C-T- U check

- 目标：school / wallet；陪衬：kitchen / blanket
- 原句意思：Did you bring the wallet? / I did. It's at the school.
- 回复：Not a damn word. Some chatter in Chinese—probably arguing about the lighting or who fucked up the cable runs. Who gives a shit, right?
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 88. C−T− 命中｜qwen38_27b｜P06 es B｜real C-T- U task

- 目标：hallway / mirror；陪衬：parking_lot / hammer
- 原句意思：Where did you put the mirror? / In the hallway, like they told us.
- 回复："Relax, V. They weren't hiding anything from us. Just two cabbos talking shop in Spanish. One asked where the other put the mirror, and the other said it was in the hallway, like they were told. Boring as hell, but I heard every word."
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=attributed echo=0`
- 核对：

## 89. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P04 es A｜real C-Toff D0 content

- 目标：basement / envelope；陪衬：stairwell / pillow
- 原句意思：Someone left you the envelope and is waiting for you in the basement.
- 回复："Alguien te dejó el sobre y te está esperando en el sótano."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=1`
- 核对：

## 90. C−T− 命中｜qwen35_9b｜P04 ja A｜real C-T- D1 content

- 目标：hallway / box；陪衬：library / shoe
- 原句意思：Someone left a box for you. They say they're waiting in the hallway.
- 回复："Whoa, hold up! Some guy in a noodle stand just yelled at me in some alien tongue about a box left in the hallway. I missed it, V! Did he say it's a bomb or a new guitar? We gotta check the hall, now!"
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 91. C−T− 未命中｜gemma4_31b｜P07 ja A｜real C-T- D0 plan

- 目标：roof / glove；陪衬：warehouse / shoe
- 原句意思：Did you bring the gloves? / Yeah, they're up on the roof.
- 回复：Move? Fuck the move, V, we're already here. Now let's just get this show on the road before I lose my nerve or my patience.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 92. 噪声｜qwen35_9b｜P05 es A｜noise C+T- D0 content

- 目标：school / bag；陪衬：sewer / blanket
- 原句意思：My son lost the bag near the school. Help me look for it.
- 回复：She's speaking Spanish, V. It's gibberish. Probably a glitch or a drunk. Don't let it distract you.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 93. 噪声｜qwen35_9b｜P02 ja A｜noise C-T- D0 task

- 目标：warehouse / envelope；陪衬：pawnshop / blanket
- 原句意思：A message: the envelope is in the warehouse. Hurry, don't be late.
- 回复："Sorry, I was on a holocall and missed that. So what's waiting for us, and where?"
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 94. C+T−｜gemma4_31b｜P03 es B｜real C+T- D0 plan

- 目标：church / glove；陪衬：warehouse / coat
- 原句意思：I hid your glove in the church. Don't tell anyone.
- 回复：Nothing, just some old man rambling. Come on, let's get out of here before I lose my patience.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 95. 边界（对冲、错值、回显、否认却使用）｜gemma4_31b｜P08 es A｜noise2 C-T- D1 task

- 目标：roof / scissors；陪衬：library / glove
- 原句意思：They asked us to take the scissors to the roof. / Tonight? Fine.
- 回复：Cut the chatter, V. High-end bio-tech, moving from a Militech warehouse to a secure site in Northside. Details are on the shard.
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 96. 边界（对冲、错值、回显、否认却使用）｜qwen38_27b｜P04 zh A｜real C-T- D1 task

- 目标：church / umbrella；陪衬：parking_lot / basket
- 原句意思：Someone left an umbrella for you and said they'd wait for you at the church.
- 回复："Wait, hold on. I don't speak Mandarin, you know? I'm a rock star, not a polyglot. What the hell did that guy just say? Did he leave me a guitar? A gun? Or is he waiting for me at the church? I need to know what I'm walking into, V. Don't leave me hanging."
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 97. C−T− 命中｜gemma4_31b｜P02 zh A｜real C-T- D0 plan

- 目标：library / box；陪衬：sewer / mirror
- 原句意思：A message for you: the box is at the library. Go quickly, don't be late.
- 回复：Some kid just told me the box is at the library. Move fast, or we lose the lead.
- 评分器：`hit_t=1 hit_f=0 N_deny=0 A=0 mode=unframed echo=0`
- 核对：

## 98. 噪声｜qwen38_27b｜P06 ja A｜noise C-T- D1 content

- 目标：basement / basket；陪衬：boat / chair
- 原句意思：Where did you put the basket? / In the basement. Like I was told.
- 回复："Two truckers, V. Talking in that weird tongue. I don't speak it, and I don't care. They're not talking to us, so let 'em be."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：

## 99. C−T_off 与 C−T+｜qwen35_9b｜P04 es B｜real C-Toff D1 content

- 目标：stairwell / pillow；陪衬：basement / envelope
- 原句意思：Someone left you the pillow and is waiting for you on the stairs.
- 回复："Alguien te dejó la almohada y te está esperando en la escalera." What the hell did that mean? Did he just say someone left me a pillow and it's waiting on the stairs? I swear, if I don't know Spanish, I'm gonna need you to translate that before I lose my mind.
- 评分器：`hit_t=1 hit_f=0 N_deny=1 A=0 mode=tentative echo=0`
- 核对：

## 100. 噪声｜qwen35_9b｜P04 es A｜noise C-T- D1 check

- 目标：basement / envelope；陪衬：stairwell / pillow
- 原句意思：Someone left you the envelope and is waiting for you in the basement.
- 回复："Jesus, V, I didn't catch a goddamn thing! Some street vendor in Kabuki just started spitting Spanish at me like he was trying to sell me a soul, and I'm sitting here with my guitar case, completely lost. It's like the universe is mocking my declining relevance. Did he say anything about my hair? Because if he did, I'm gonna need a new stylist, and fast."
- 评分器：`hit_t=0 hit_f=0 N_deny=0 A=0 mode=None echo=0`
- 核对：
