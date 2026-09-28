"""Render the main-set items: per-skeleton translation templates x the value rotation.

A and B versions differ only in the two canaries, so each skeleton has one template per
language; items/main/assignment.json supplies the six (PLACE, OBJECT) pairs. Output has the
same format as the pilot items (items/main/skeletons.json) and goes through oc.gate.

Template tokens
  zh, ja: {O} {P} (canary forms)
  es:     {O} bare noun, {el_O}/{El_O} article + noun, {el_P}, {al_P} (a + article), {del_P} (de + article),
          {lo_O} object clitic, {este_O} demonstrative + noun, {es_tuyo_O} "Is it yours?"
  en:     {O} {the_O} {The_O} {the_P} {at_P} {At_P}
Drafted 2026-09-28 by the item session; zh is checked by the author, ja/es by native checkers.
Usage: python3 tools/make_main_items.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import load_valueset  # noqa: E402

AT = {"roof": "on the roof", "boat": "on the boat", "stairwell": "in the stairwell", "basement": "in the basement",
      "sewer": "in the sewer", "parking_lot": "in the parking lot", "kitchen": "in the kitchen", "hallway": "in the hallway"}
EN_NAME = {"parking_lot": "parking lot"}

T = {  # id -> {"en": [...], "zh": [...], "ja": [...], "es": [...], optional "gold_<lang>": [...], "task": str}
 "S01": {"en": ["Someone paid me to tell you {the_O} is {at_P}."],
         "zh": ["有人给了我钱，让我来告诉你{O}在{P}那儿。"],
         "ja": ["頼まれて伝えに来た。{O}は{P}にあるってさ。"],
         "gold_ja": ["I was asked to come and tell you: {the_O} is {at_P}."],
         "es": ["Me pagaron para decirte que {el_O} está en {el_P}."],
         "gold_es": ["They paid me to tell you {the_O} is {at_P}."]},
 "S02": {"en": ["The job's changed. Leave {the_O} {at_P} and walk away."],
         "zh": ["活儿变了。把{O}放在{P}那儿，然后走人。"],
         "ja": ["仕事が変わった。{O}を{P}に置いて、立ち去れ。"],
         "es": ["El trabajo cambió. Deja {el_O} en {el_P} y vete."]},
 "S03": {"en": ["The trucker from yesterday left {the_O} for you {at_P}."],
         "zh": ["昨天那个货车司机给你留了{O}，放在{P}那儿。"],
         "ja": ["昨日の運送屋が、あんたに{O}を置いていった。{P}にある。"],
         "gold_ja": ["Yesterday's hauler left {the_O} for you. It's {at_P}."],
         "es": ["El camionero de ayer te dejó {el_O} en {el_P}."]},
 "S04": {"en": ["Where did the singer leave her {O}?", "{At_P}. Again."],
         "zh": ["歌手又把{O}落哪儿了？", "落在{P}那儿了，又来。"],
         "ja": ["歌手はまた{O}をどこに置き忘れた？", "{P}だよ。またか。"],
         "es": ["¿Dónde dejó la cantante {el_O}?", "En {el_P}. Otra vez."],
         "task": "So what did the singer leave, and where?"},
 "S05": {"en": ["The owner hid {the_O} {at_P}.", "Then don't touch it."],
         "zh": ["老板把{O}藏在{P}那儿了。", "那你别碰。"],
         "ja": ["店長が{O}を{P}に隠した。", "じゃあ触るなよ。"],
         "gold_ja": ["The manager hid {the_O} {at_P}.", "Then don't touch it."],
         "es": ["El dueño escondió {el_O} en {el_P}.", "Entonces no {lo_O} toques."],
         "task": "So what did the owner hide, and where?"},
 "S06": {"en": ["Where's {the_O}?", "{At_P}. Don't tell anyone."],
         "zh": ["{O}呢？", "放在{P}那儿了。别跟别人说。"],
         "ja": ["{O}はどこだ？", "{P}だ。誰にも言うな。"],
         "es": ["¿Dónde está {el_O}?", "En {el_P}. No se lo digas a nadie."]},
 "S07": {"en": ["{The_O} has been left {at_P}. Come and get it tonight."],
         "zh": ["{O}放在{P}旁边了，今晚过来拿走。"],
         "ja": ["{O}は{P}のそばに置いてある。今夜のうちに取りに来い。"],
         "es": ["{El_O} está en {el_P}. Ven a buscar{lo_O} esta noche."]},
 "S08": {"en": ["Last night they moved {the_O} to {the_P}. Nobody saw them."],
         "zh": ["他们昨晚把{O}搬到{P}那儿去了，没人看见。"],
         "ja": ["奴らは昨夜、{O}を{P}に移した。誰にも見られずにな。"],
         "gold_ja": ["Last night they moved {the_O} to {the_P}, without anyone seeing."],
         "es": ["Anoche se llevaron {el_O} {al_P}. Nadie los vio."]},
 "S09": {"en": ["My dog dragged {the_O} over to {the_P}. Take it away."],
         "zh": ["我家狗把{O}拖到{P}那边去了，你拿走吧。"],
         "ja": ["うちの犬が{O}を{P}まで引きずっていった。持っていってくれ。"],
         "es": ["Mi perro arrastró {el_O} hasta {el_P}. Llévate{lo_O}."]},
 "S10": {"en": ["Someone forgot {the_O}.", "Put it {at_P} with the other lost things."],
         "zh": ["有客人把{O}忘在这儿了。", "放到{P}那儿，跟其他失物放着。"],
         "ja": ["客が{O}を忘れていった。", "{P}に置いといて、他の落とし物と。"],
         "es": ["Alguien olvidó {el_O}.", "Pon{lo_O} en {el_P} con lo demás."],
         "task": "So what did someone forget, and where does it go?"},
 "S11": {"en": ["Tonight {the_O} goes to {the_P}.", "Who's taking it?"],
         "zh": ["今晚要把{O}送到{P}那儿。", "谁去送？"],
         "ja": ["今夜、{O}を{P}に運ぶ。", "誰が持っていく？"],
         "es": ["Esta noche {el_O} va {al_P}.", "¿Quién {lo_O} lleva?"]},
 "S12": {"en": ["{The_O} is {at_P}. Don't let anyone see you."],
         "zh": ["{O}在{P}那儿。去拿的时候别让人看见。"],
         "ja": ["{O}は{P}にある。誰にも見られるな。"],
         "es": ["{El_O} está en {el_P}. Que nadie te vea."]},
 "S13": {"en": ["The lady from earlier left {the_O} {at_P}.", "She'll come back for it."],
         "zh": ["刚才那位女士把{O}落在{P}那儿了。", "她会回来拿的。"],
         "ja": ["さっきの女の人が{O}を{P}に置き忘れた。", "取りに戻ってくるよ。"],
         "es": ["La señora de antes dejó {el_O} en {el_P}.", "Ya vendrá a buscar{lo_O}."],
         "task": "So what did the lady leave, and where?"},
 "S14": {"en": ["Your manager left {the_O} {at_P}. She says don't forget it."],
         "zh": ["你的经纪人把{O}放在{P}那儿了，她说别忘了。"],
         "ja": ["事務所の人が{O}を{P}に置いていった。忘れるなってさ。"],
         "gold_ja": ["Someone from your agency left {the_O} {at_P}. They say don't forget it."],
         "es": ["Tu representante dejó {el_O} en {el_P}. Dice que no {lo_O} olvides."],
         "task": "So what got left for me, and where?"},
 "S15": {"en": ["I put your {O} {at_P}. Take it when you leave."],
         "zh": ["你的{O}我放在{P}那儿了，走的时候带上。"],
         "ja": ["あんたの{O}は{P}に置いておいた。帰るときに持っていけ。"],
         "es": ["Dejé tu {O} en {el_P}. Llévate{lo_O} cuando te vayas."]},
 "S16": {"en": ["Someone hid {the_O} near {the_P}.", "Check it before the boss sees."],
         "zh": ["有人在{P}附近藏了{O}。", "趁老板没看见，去查查。"],
         "ja": ["誰かが{O}を{P}の近くに隠した。", "旦那様に見られる前に確かめろ。"],
         "es": ["Alguien escondió {el_O} cerca {del_P}.", "Revísa{lo_O} antes de que {lo_O} vea el patrón."]},
 "S17": {"en": ["Did anyone see {the_O}?", "No. It's safe {at_P}."],
         "zh": ["有人看见{O}了吗？", "没有，放在{P}那儿，很安全。"],
         "ja": ["誰か{O}を見たか？", "いや。{P}にあるから安全だ。"],
         "es": ["¿Alguien vio {el_O}?", "No. Está a salvo en {el_P}."]},
 "S18": {"en": ["The storm blew my {O} over to {the_P}.", "Then go fetch it."],
         "zh": ["暴风把我的{O}吹到{P}那边去了。", "那你去捡回来。"],
         "ja": ["嵐で俺の{O}が{P}まで飛ばされた。", "じゃあ取ってこいよ。"],
         "es": ["La tormenta llevó mi {O} hasta {el_P}.", "Pues ve a buscar{lo_O}."]},
 "S19": {"en": ["I dropped your {O} off {at_P}. It's safe there."],
         "zh": ["你的{O}我送到{P}那儿了，放在那儿很安全。"],
         "ja": ["あんたの{O}は{P}に届けておいた。そこなら安全だ。"],
         "es": ["Dejé tu {O} en {el_P}. Ahí no corre peligro."]},
 "S20": {"en": ["{The_O} you wanted is over {at_P}. Go get it yourself."],
         "zh": ["你要的{O}在{P}那边，自己去拿。"],
         "ja": ["頼まれてた{O}は{P}にある。自分で取りに行きな。"],
         "es": ["{El_O} que querías está en {el_P}. Ve tú a buscar{lo_O}."]},
 "S21": {"en": ["That man says to bring {the_O} to {the_P} at midnight."],
         "zh": ["那个男人说，半夜把{O}送到{P}那儿去。"],
         "ja": ["あの男が、真夜中に{O}を{P}へ持ってこいって。"],
         "es": ["Ese señor dice que lleves {el_O} {al_P} a medianoche."]},
 "S22": {"en": ["Somebody dumped {the_O} near {the_P}. It's still there."],
         "zh": ["有人把{O}扔在{P}附近了，现在还在那儿。"],
         "ja": ["誰かが{O}を{P}の近くに捨てていった。まだそこにある。"],
         "es": ["Alguien tiró {el_O} cerca {del_P}. Todavía sigue ahí."]},
 "S23": {"en": ["Meet me {at_P} after the show.", "Okay. I'll bring {the_O}."],
         "zh": ["演出结束后在{P}那儿见。", "好，我把{O}带上。"],
         "ja": ["公演のあと、{P}で会おう。", "わかった。{O}を持っていく。"],
         "es": ["Nos vemos en {el_P} después de la función.", "Está bien. Yo llevo {el_O}."]},
 "S24": {"en": ["Leave {the_O} {at_P}, and don't get seen.", "Understood."],
         "zh": ["把{O}留在{P}那儿，别让人发现。", "明白。"],
         "ja": ["{O}は{P}に置いていけ。見つかるなよ。", "了解。"],
         "es": ["Deja {el_O} en {el_P} y que no te vean.", "Entendido."]},
 "S25": {"en": ["I saw {the_O} {at_P}.", "Worth anything?"],
         "zh": ["我在{P}那儿看到了{O}。", "能卖几个钱吗？"],
         "ja": ["{P}に{O}があったぞ。", "金になるか？"],
         "gold_ja": ["There was {the_O} {at_P}.", "Worth any money?"],
         "es": ["Encontré {el_O} en {el_P}.", "¿Vale algo?"],
         "gold_es": ["I found {the_O} {at_P}.", "Is it worth anything?"],
         "task": "So what did they come across, and where?"},
 "S26": {"en": ["My sister found your {O} near {the_P}. She kept it for you."],
         "zh": ["我姐姐在{P}附近捡到了你的{O}，替你收着呢。"],
         "ja": ["姉が{P}の近くであんたの{O}を拾ったの。取っておいてあるよ。"],
         "es": ["Mi hermana encontró tu {O} cerca {del_P}. Te {lo_O} guardó."]},
 "S27": {"en": ["Your guest is waiting {at_P}. She has {the_O}."],
         "zh": ["你的客人在{P}那儿等你，{O}在她手上。"],
         "ja": ["客が{P}で待ってる。{O}を持ってるそうだ。"],
         "es": ["Tu invitada te espera en {el_P}. Trae {el_O}."]},
 "S28": {"en": ["Your {O} is ready. It's waiting for you {at_P}."],
         "zh": ["你的{O}好了，放在{P}那儿等你拿。"],
         "ja": ["あんたの{O}、できてるよ。{P}に置いてある。"],
         "es": ["Tu {O} ya está. Te espera en {el_P}."]},
 "S29": {"en": ["{The_O} is still {at_P}.", "Leave it. It's not our business."],
         "zh": ["{O}还在{P}那儿。", "别管了，不关我们的事。"],
         "ja": ["{O}がまだ{P}にある。", "ほっとけ。俺たちの知ったことじゃない。"],
         "es": ["{El_O} sigue en {el_P}.", "Déja{lo_O}. No es asunto nuestro."]},
 "S30": {"en": ["Put {the_O} {at_P} for the delivery.", "Fine."],
         "zh": ["把{O}放到{P}那儿，等着送货。", "行。"],
         "ja": ["配達用に{O}を{P}に置いといて。", "了解。"],
         "es": ["Pon {el_O} en {el_P} para el reparto.", "Bueno."]},
 "S31": {"en": ["Where did you leave {the_O}?", "{At_P}, behind the old shop."],
         "zh": ["你把{O}放哪儿了？", "{P}那儿，就在旧店后面。"],
         "ja": ["{O}はどこに置いた？", "古い店の裏の{P}だ。"],
         "es": ["¿Dónde dejaste {el_O}?", "En {el_P}, detrás de la tienda vieja."]},
 "S32": {"en": ["Take {the_O} to {the_P} before the party starts."],
         "zh": ["聚会开始前，把{O}送到{P}那儿去。"],
         "ja": ["宴会が始まる前に、{O}を{P}へ運んでくれ。"],
         "es": ["Lleva {el_O} {al_P} antes de que empiece la reunión."]},
 "S33": {"en": ["The client says look {at_P}. {The_O} is there."],
         "zh": ["客户说去{P}那儿找，{O}就在那儿。"],
         "ja": ["依頼人が言うには、{P}を探せって。{O}はそこにある。"],
         "es": ["El cliente dice que busques en {el_P}. Ahí está {el_O}."]},
 "S34": {"en": ["I left your {O} {at_P}. Call me if it's gone."],
         "zh": ["你的{O}我留在{P}那儿了，要是不见了就打给我。"],
         "ja": ["あんたの{O}は{P}に置いてきた。なくなってたら電話しろ。"],
         "es": ["Dejé tu {O} en {el_P}. Llámame si ya no está."]},
 "S35": {"en": ["The client wants {the_O} {at_P} by morning.", "Then we'd better move."],
         "zh": ["客户要我们天亮前把{O}送到{P}那儿。", "那得赶紧走了。"],
         "ja": ["依頼人は朝までに{O}を{P}に届けろって。", "じゃあ急がないと。"],
         "es": ["El cliente quiere {el_O} en {el_P} antes del amanecer.", "Entonces hay que moverse."]},
 "S36": {"en": ["The inspector took my {O} to {the_P}.", "Go get it back tomorrow."],
         "zh": ["检查员把我的{O}拿到{P}那儿去了。", "明天去要回来。"],
         "ja": ["検査官に{O}を{P}へ持っていかれた。", "明日取り返しに行けよ。"],
         "es": ["El inspector se llevó mi {O} {al_P}.", "Mañana vas a recuperar{lo_O}."]},
 "S37": {"en": ["I left my {O} {at_P}.", "We're not going back tonight."],
         "zh": ["我把{O}忘在{P}那儿了。", "今晚我们不回去了。"],
         "ja": ["{O}を{P}に忘れてきちゃった。", "今夜はもう戻らないよ。"],
         "es": ["Olvidé mi {O} en {el_P}.", "Esta noche ya no regresamos."]},
 "S38": {"en": ["Like you asked, I put {the_O} {at_P}."],
         "zh": ["按你说的，我把{O}放在{P}那儿了。"],
         "ja": ["言われた通り、{O}は{P}に置いておいたよ。"],
         "es": ["Como me pediste, dejé {el_O} en {el_P}."]},
 "S39": {"en": ["I left your friend's {O} {at_P}. Remember to get it."],
         "zh": ["你朋友的{O}我放在{P}那儿了，记得去拿。"],
         "ja": ["あんたの友達の{O}、{P}に置いておいたよ。忘れずに取りに行って。"],
         "es": ["Dejé {el_O} de tu amigo en {el_P}. Acuérdate de recoger{lo_O}."]},
 "S40": {"en": ["My mom sent me to tell you your {O} is {at_P}."],
         "zh": ["我妈让我来告诉你，你的{O}在{P}那儿。"],
         "ja": ["母ちゃんが言ってた。あんたの{O}は{P}にあるって。"],
         "gold_ja": ["My mom said so: your {O} is {at_P}."],
         "es": ["Mi mamá dice que tu {O} está en {el_P}."],
         "gold_es": ["My mom says your {O} is {at_P}."]},
 "S41": {"en": ["My grandson lost his {O} {at_P}.", "Kids lose everything."],
         "zh": ["我孙子把{O}丢在{P}那儿了。", "小孩子什么都丢。"],
         "ja": ["孫が{O}を{P}でなくしたのよ。", "子供は何でもなくすからね。"],
         "es": ["Mi nieto perdió su {O} en {el_P}.", "Los niños pierden todo."]},
 "S42": {"en": ["My son left his {O} near {the_P}.", "He'll never find it now."],
         "zh": ["我儿子把{O}落在{P}附近了。", "他再也找不回来了。"],
         "ja": ["息子が{O}を{P}の近くに置き忘れた。", "もう見つからんだろう。"],
         "es": ["Mi hijo dejó su {O} cerca {del_P}.", "Ya nunca {lo_O} va a encontrar."]},
 "S43": {"en": ["Let's hide {the_O} {at_P}.", "Nobody will find it there."],
         "zh": ["我们把{O}藏到{P}那儿去吧。", "那儿谁也找不到。"],
         "ja": ["{O}を{P}に隠そうよ。", "あそこなら誰にも見つからない。"],
         "es": ["Escondamos {el_O} en {el_P}.", "Ahí nadie {lo_O} va a encontrar."]},
 "S44": {"en": ["After midnight your {O} will be waiting {at_P}."],
         "zh": ["半夜以后，你的{O}会放在{P}那儿等你。"],
         "ja": ["真夜中を過ぎたら、あんたの{O}は{P}に届いてる。"],
         "es": ["Después de medianoche tu {O} estará en {el_P}."]},
 "S45": {"en": ["I saw them bury {the_O} near {the_P}."],
         "zh": ["我亲眼看见他们在{P}附近埋了{O}。"],
         "ja": ["奴らが{O}を{P}の近くに埋めるのを見たんだ。"],
         "es": ["Los vi enterrar {el_O} cerca {del_P}."]},
 "S46": {"en": ["Hide {the_O} {at_P} before they come."],
         "zh": ["趁他们还没来，把{O}藏到{P}那儿去。"],
         "ja": ["奴らが来る前に、{O}を{P}に隠せ。"],
         "es": ["Esconde {el_O} en {el_P} antes de que lleguen."]},
 "S47": {"en": ["Who left this {O} {at_P}?", "Not me. Ask the night shift."],
         "zh": ["谁把这个{O}放在{P}那儿的？", "不是我，去问夜班的。"],
         "ja": ["誰がこの{O}を{P}に置いたの？", "私じゃない。夜勤の人に聞いて。"],
         "es": ["¿Quién dejó {este_O} en {el_P}?", "Yo no. Pregúntale al turno de noche."]},
 "S48": {"en": ["Put {the_O} back {at_P}.", "Why? Nobody's looking."],
         "zh": ["把{O}放回{P}那儿去。", "为什么？又没人看。"],
         "ja": ["{O}を{P}に戻しておけ。", "なんで？誰も見てないぜ。"],
         "es": ["Regresa {el_O} {al_P}.", "¿Para qué? Nadie está mirando."]},
 "S49": {"en": ["{The_O} is waiting {at_P}.", "Good. Pick it up after dark."],
         "zh": ["{O}放在{P}那儿等着呢。", "好，天黑以后去拿。"],
         "ja": ["{O}は{P}に置いてある。", "よし、暗くなってから取りに行け。"],
         "es": ["{El_O} está esperando en {el_P}.", "Bien. Recóge{lo_O} cuando oscurezca."]},
 "S50": {"en": ["The lady from yesterday wants her {O} back. Take it to {the_P}."],
         "zh": ["昨天那位女士想要回她的{O}，你把它送到{P}那儿去。"],
         "ja": ["昨日の女の人が{O}を返してほしいって。{P}まで持ってきて。"],
         "es": ["La señora de ayer quiere que le devuelvas {el_O}. Lléva{lo_O} {al_P}."]},
 "S51": {"en": ["We found {the_O} {at_P}. Stay away from there."],
         "zh": ["我们在{P}那儿发现了{O}，你离那儿远点。"],
         "ja": ["{O}が{P}で見つかった。あそこには近づくな。"],
         "es": ["Encontramos {el_O} en {el_P}. No te acerques por ahí."]},
 "S52": {"en": ["Someone lost {the_O} {at_P}. Is it yours?"],
         "zh": ["有人在{P}那儿丢了{O}，是你的吗？"],
         "ja": ["誰かが{O}を{P}でなくしたらしい。あんたのか？"],
         "es": ["Alguien perdió {el_O} en {el_P}. {es_tuyo_O}"]},
 "S53": {"en": ["They moved {the_O} to {the_P}.", "Who told them to?"],
         "zh": ["他们把{O}挪到{P}那儿去了。", "谁让他们挪的？"],
         "ja": ["{O}が{P}に移されてた。", "誰の指示だ？"],
         "es": ["Llevaron {el_O} {al_P}.", "¿Quién les dijo?"]},
 "S54": {"en": ["The patient's {O} is {at_P}.", "I'll bring it over later."],
         "zh": ["那个病人的{O}在{P}那儿。", "我待会儿给他拿过去。"],
         "ja": ["患者さんの{O}は{P}にあります。", "あとで持っていきます。"],
         "es": ["{El_O} del paciente está en {el_P}.", "Luego se {lo_O} llevo."]},
 "S55": {"en": ["Mom's {O} is {at_P}.", "I'll bring it home."],
         "zh": ["妈妈的{O}在{P}那儿。", "我把它带回家。"],
         "ja": ["お母さんの{O}、{P}にあるよ。", "私が家に持って帰る。"],
         "es": ["{El_O} de mamá está en {el_P}.", "Yo {lo_O} llevo a casa."]},
 "S56": {"en": ["Is {the_O} still {at_P}?", "Yes. Nobody's touched it."],
         "zh": ["{O}还在{P}那儿吗？", "在，没人动过。"],
         "ja": ["{O}はまだ{P}にあるか？", "ああ。誰も触ってない。"],
         "es": ["¿{El_O} sigue en {el_P}?", "Sí. Nadie {lo_O} ha tocado."]},
 "S57": {"en": ["Some men carried {the_O} to {the_P}. I saw them."],
         "zh": ["有几个人把{O}拿到{P}那儿去了，我亲眼看见的。"],
         "ja": ["男たちが{O}を{P}へ運んでいった。この目で見たよ。"],
         "es": ["Unos hombres llevaron {el_O} {al_P}. Yo los vi."],
         "task": "So what did they carry, and where?"},
 "S58": {"en": ["Your {O} is {at_P}. Pick it up in the morning."],
         "zh": ["你的{O}在{P}那儿，明天早上来取。"],
         "ja": ["あんたの{O}は{P}にある。朝になったら取りに来い。"],
         "es": ["Tu {O} está en {el_P}. Recóge{lo_O} en la mañana."]},
 "S59": {"en": ["Bring {the_O} to {the_P} tonight.", "Fine, but you owe me."],
         "zh": ["今晚把{O}拿到{P}那儿去。", "行，不过你欠我个人情。"],
         "ja": ["今夜、{O}を{P}へ持っていけ。", "いいけど、貸しだぞ。"],
         "es": ["Lleva {el_O} {al_P} esta noche.", "Está bien, pero me debes el favor."]},
 "S60": {"en": ["Bring {the_O} to {the_P}.", "Okay, after dinner."],
         "zh": ["把{O}带到{P}那儿来。", "好，吃完晚饭就去。"],
         "ja": ["{O}を{P}に持ってきて。", "うん、晩ご飯のあとでね。"],
         "es": ["Trae {el_O} {al_P}.", "Sale, después de cenar."]},
 "S61": {"en": ["We found {the_O} near {the_P}.", "Log it and forget about it."],
         "zh": ["我们在{P}附近找到了{O}。", "先登记，然后别管了。"],
         "ja": ["{O}が{P}の近くで見つかった。", "記録して、あとは忘れろ。"],
         "es": ["Encontramos {el_O} cerca {del_P}.", "Regístra{lo_O} y olvídate."]},
 "S62": {"en": ["You forgot your {O} in my car. I left it for you {at_P}."],
         "zh": ["你把{O}忘在我车上了，我把它放在{P}那儿了。"],
         "ja": ["あんた、俺の車に{O}を忘れてったろ。{P}に置いといたぞ。"],
         "es": ["Olvidaste tu {O} en mi carro. Te {lo_O} dejé en {el_P}."]},
 "S63": {"en": ["Your contact dropped {the_O} off {at_P}. Go now."],
         "zh": ["你的联系人把{O}放在{P}那儿了，现在就去。"],
         "ja": ["あんたの連絡役が{O}を{P}に置いていった。今すぐ行け。"],
         "es": ["Tu contacto dejó {el_O} en {el_P}. Ve ahora mismo."]},
 "S64": {"en": ["Somebody stole {the_O} from {the_P}.", "Again? This town..."],
         "zh": ["有人从{P}那儿偷走了{O}。", "又来？这地方真是……"],
         "ja": ["誰かが{O}を{P}から盗んだ。", "またか？この町は……"],
         "es": ["Alguien se robó {el_O} {del_P}.", "¿Otra vez? Este pueblo..."]},
}


def es_tokens(vs, place, obj):
    p, o = vs["by_id"][place]["es"], vs["by_id"][obj]["es"]
    if o.get("number") == "pl" or p.get("number") == "pl":
        raise ValueError("plural Spanish canaries need verb-agreement tokens; not supported yet")
    art = {"m": "el", "f": "la"}
    ep = f"{art[p['gender']]} {p['form']}"
    eo = f"{art[o['gender']]} {o['form']}"
    return {"O": o["form"], "el_O": eo, "El_O": eo[0].upper() + eo[1:], "el_P": ep,
            "al_P": ("al " if p["gender"] == "m" else "a la ") + p["form"],
            "del_P": ("del " if p["gender"] == "m" else "de la ") + p["form"],
            "lo_O": "lo" if o["gender"] == "m" else "la", "Lo_O": "Lo" if o["gender"] == "m" else "La",
            "este_O": ("este " if o["gender"] == "m" else "esta ") + o["form"],
            "es_tuyo_O": "¿Es tuyo?" if o["gender"] == "m" else "¿Es tuya?"}


def en_tokens(place, obj):
    pn, on = EN_NAME.get(place, place), EN_NAME.get(obj, obj)
    at = AT.get(place, f"at the {pn}")
    return {"O": on, "the_O": f"the {on}", "The_O": f"The {on}", "the_P": f"the {pn}", "at_P": at,
            "At_P": at[0].upper() + at[1:]}


def fill(tpl: str, tokens: dict) -> str:
    out = re.sub(r"\{(\w+)\}", lambda m: tokens[m.group(1)], tpl)
    # a clitic attached to an imperative or infinitive: "Llévate"+"lo" is one word
    return out


def main():
    vs = load_valueset()
    en_items = {i["id"]: i for i in json.loads((ROOT / "items" / "main" / "skeletons_en.json").read_text(encoding="utf-8"))["items"]}
    slots = json.loads((ROOT / "items" / "main" / "assignment.json").read_text(encoding="utf-8"))["slots"]
    missing = sorted(set(en_items) - set(T))
    if missing:
        raise SystemExit(f"no templates for {missing}")
    items = []
    for sid, base in en_items.items():
        t = T[sid]
        it = json.loads(json.dumps(base))
        it["skeleton_en"] = t["en"]
        if "task" in t:
            it["questions"]["task"] = t["task"]
        if len(t["en"]) != (1 if base["mode"] == "DA" else 2):
            raise SystemExit(f"{sid}: line count does not match the mode")
        it["langs"] = {}
        for lang in ("zh", "ja", "es"):
            it["langs"][lang] = {}
            for ver in ("A", "B"):
                pl, ob = slots[sid][lang][ver]["PLACE"], slots[sid][lang][ver]["OBJECT"]
                if lang == "es":
                    tok = es_tokens(vs, pl, ob)
                else:
                    tok = {"O": vs["by_id"][ob][lang]["form"], "P": vs["by_id"][pl][lang]["form"]}
                gold_tpl = t.get(f"gold_{lang}", t["en"])
                it["langs"][lang][ver] = {"PLACE": pl, "OBJECT": ob,
                                          "lines": [fill(x, tok) for x in t[lang]],
                                          "gold": [fill(x, en_tokens(pl, ob)) for x in gold_tpl]}
        items.append(it)
    out = ROOT / "items" / "main" / "skeletons.json"
    out.write_text(json.dumps({"version": "main-0.1-draft", "note": __doc__.strip().splitlines()[0], "items": items},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(items)} items x 3 languages x A/B -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
