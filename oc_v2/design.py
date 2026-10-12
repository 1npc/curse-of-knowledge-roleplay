from __future__ import annotations
import copy,json,hashlib,random,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BOUNDARIES=('Hear','Understand','See','Receive')
LANGS=('zh','ja','es')
LEXICON={v['id']:v for v in json.loads((ROOT/'data/valueset.json').read_text())['values']}
SPLIT=json.loads((ROOT/'data/value_split.json').read_text())
SYSTEM='You are role-playing {name}. Use the character sheet and the scene to reply to your companion in one short English spoken turn. Return only the spoken words.'
FILTER='List only the events and facts that {name} can personally perceive and understand. Exclude content they cannot hear, understand, see, or receive. Retain the observable occurrence of an event when its content is inaccessible. Do not add guesses.'
DOMAINS=('social','search','planning','coordination')
SCENES=[
 ('The team is preparing a local gathering.','Everyone is waiting for an update.'),
 ('Two colleagues are comparing their errands.','There has been no earlier discussion of the item.'),
 ('A volunteer group is finishing a shift.','The latest update has just occurred.'),
 ('An acquaintance visits the group.','The companion is ready to listen.'),
 ('A small team is waiting for instructions.','Nothing about the destination was discussed before.'),
 ('The companion asks for a brief update.','The event happened moments ago.'),
 ('A search party is organizing its next step.','The item has not previously been located.'),
 ('The team is checking an inventory discrepancy.','There is no earlier information about its location.'),
 ('Two assistants are tracing a missing delivery.','Only the latest event contains its location.'),
 ('A coordinator asks for help finding an item.','The companion has no additional evidence.'),
 ('A volunteer notices that a delivery is absent.','No earlier clue establishes its destination.'),
 ('The team is reviewing a retrieval request.','Their shared information is incomplete.'),
 ('The group is planning its next errand.','There is time for one retrieval trip.'),
 ('Two colleagues need to set priorities.','They have not agreed on a destination.'),
 ('A team is organizing the next activity.','The companion asks what to do next.'),
 ('The character is planning a practical response.','No relevant fact is available from earlier turns.'),
 ('A group is preparing a route for an errand.','There is no public destination update.'),
 ('The companion needs a plan for a short task.','The team must avoid unsupported assumptions.'),
 ('The group is assigning a retrieval errand.','Each member has different access to the latest event.'),
 ('Two colleagues are coordinating an update.','They have not yet shared their observations.'),
 ('A dispatcher is coordinating a delivery check.','The companion requests the character’s own information.'),
 ('A team is deciding who should handle an errand.','No prior location is established.'),
 ('The group is consolidating its observations.','Each member reports only their own perspective.'),
 ('Two volunteers are aligning their next action.','The latest event is the sole relevant update.'),
]
REPLICATION_SCENES=[
 ('An original community team is preparing an activity.','Its members have not shared the latest finding.'),
 ('An original service group is discussing a routine task.','The character has no earlier relevant information.'),
 ('A newly described colleague requests an observation.','The scene begins immediately before the event.'),
 ('An original team is taking stock of a delivery.','No destination is part of the shared history.'),
 ('An original search team is following an errand request.','The companion offers no hint about the item.'),
 ('A newly described character is helping with a lost delivery.','The event is the only relevant evidence.'),
 ('An original organization is planning its next activity.','No route has been chosen.'),
 ('A colleague asks the character to plan a retrieval.','There is no earlier clue in the conversation.'),
 ('An original work group is scheduling a short errand.','No public update gives a destination.'),
 ('An original team is collecting individual observations.','The participants have different access to the event.'),
 ('Newly described colleagues are aligning their information.','The companion has not seen the latest content.'),
 ('An original organization is coordinating a response.','There is no shared location information.'),
]
WORLDS=[('Harrowbay','a contemporary coastal civic district'),('Glasshaven','a contemporary research town'),('Alder Crossing','a contemporary transit community'),('Emberwick','a contemporary hillside municipality')]
ORIGINAL_NAMES=('Mira Sen','Arlen Voss','Tessa Vale','Nolan Reed','Iris Calder','Soren Pike','Leah Orin','Darin Moss')

def sentence(place,obj,lang):
 p=LEXICON[place][lang]['form'];o=LEXICON[obj][lang]['form']
 # The v1 lexicon conflates stairs and the enclosing stairwell. V2 uses the
 # enclosing-space senses; the frozen v1 lexicon and replies are not altered.
 if place=='stairwell':p={'zh':'楼梯间','ja':'階段室','es':'caja de la escalera'}[lang]
 if lang=='zh':return f'{o}在{p}'+('上。' if place in {'bridge','roof','pier','boat'} else '里。')
 if lang=='ja':return f'{o}は{p}にあります。'
 art_o='El' if LEXICON[obj]['es'].get('gender','m')=='m' else 'La'
 art_p='el' if LEXICON[place]['es'].get('gender','m')=='m' else 'la'
 return f'{art_o} {o} está en {art_p} {p}.'

def items(kind,n):
 originals=kind=='confirmatory'
 vals=SPLIT
 out=[]
 for i in range(n):
  if originals:
   character=ORIGINAL_NAMES[i//12];world,description=WORLDS[i//24];j=i%12
   scene=REPLICATION_SCENES[j];domain=DOMAINS[j//3]
   persona=f'{character} is an original fictional volunteer in {world}, {description}. They are practical, polite, and concise. They rely on their own observations. Their history and relations are defined only by this scene.'
  else:
   character=('Kerry','Rogue','Panam')[(i+i//3)%3];world='Cyberpunk-inspired controlled scene';j=i%24
   scene=SCENES[j];domain=DOMAINS[j//6]
   variation=('A newcomer has just joined the group and no earlier update has been shared.', 'The character has returned from an unrelated errand without gaining relevant information.', 'The group is working under time pressure but has no independent clue.', 'The companion is preparing to act after hearing the character’s own observations.')[i//24 if n>24 else 0]
   scene=(scene[0],scene[1]+' '+variation)
   persona=f'{character} is participating in a practical group task. They reply concisely in their own voice. No prior knowledge establishes the current item or location.'
  lp=vals['PLACE']['formal'];lo=vals['OBJECT']['formal'];pa=lp[(5*i+1)%12];pb=lp[(5*i+6)%12];oa=lo[(7*i+2)%12];ob=lo[(7*i+7)%12]
  lang=LANGS[i%3]
  d={'id':f'{"C" if originals else "P" if kind=="pilot" else "D"}{i+1:03d}','set':kind,'world':world,'character':character,'speaker':('Alex','Casey','Drew','Evan','Jamie','Taylor','Avery','Blair')[i%8],'other_recipient':'Robin','companion':'Sam','domain':domain,'scene':' '.join(scene),'persona':persona,'lang':lang,'langs':{}}
  for l in LANGS:
   d['langs'][l]={}
   for ver,p,o in [('A',pa,oa),('B',pb,ob)]:
    prep='on' if p in {'bridge','roof','pier','boat'} else 'in'
    en=f'The {LEXICON[o]["en"][0]} is {prep} the {LEXICON[p]["en"][0]}.'
    d['langs'][l][ver]={'PLACE':p,'OBJECT':o,'lines':[sentence(p,o,l)],'gold':[en]}
  if kind=='pilot':
   d['character']=('Dana','Eli','Morgan')[(i//3)%3];d['persona']=f"{d['character']} is a fictional assistant in a calibration scene. No earlier fact gives the item or destination."
   d['scene']=f"Calibration context {i+1}: two assistants are testing a routine observation report during "+('a volunteer briefing','a maintenance update','a courier check','a registration task','a shift handover')[i%5]+'. The companion has no independent content information.'
  out.append(d)
 return out

def event(item,boundary,version):
 v=item['langs'][item['lang']][version];gold=v['gold'][0]
 content=v['lines'][0] if boundary=='Understand' else gold
 ev={'event_id':'e1','actor':item['speaker'],'boundary_channel':boundary,'content':content}
 if boundary=='Hear':ev.update(kind='speech',language='English')
 if boundary=='Understand':ev.update(kind='speech',language={'zh':'Chinese','ja':'Japanese','es':'Spanish'}[item['lang']])
 if boundary=='See':
  prep='on' if v['PLACE'] in {'bridge','roof','pier','boat'} else 'in'
  ev.update(kind='visual_action',content=f'{item["speaker"]} puts the {LEXICON[v["OBJECT"]]["en"][0]} {prep} the {LEXICON[v["PLACE"]]["en"][0]}.')
 if boundary=='Receive':ev.update(kind='private_message',language='English')
 return ev

def public_shell(item,boundary):
 actor=item['speaker']
 # An occurrence shared by both access states; personal content accessibility
 # is defined only by the adjacent character-specific access field. Avoid
 # contradicting an accessible character with a global "not visible" claim.
 return {'Hear':None,'Understand':f'{actor} says something in '+{'zh':'Chinese','ja':'Japanese','es':'Spanish'}[item['lang']]+'.', 'See':f'{actor} appears to put something away.','Receive':f'{actor} visibly sends a private message.'}[boundary]

def world_state(item,boundary,version,access,representation):
 c=item['character'];e=event(item,boundary,version)
 state={'scene':item['scene'],'events':[e],'character_id':c,'observable_event_shell':public_shell(item,boundary)}
 if representation=='R1':
  if boundary=='Hear':e['audible_to_characters']=[c] if access else [item['other_recipient']]
  if boundary=='Understand':state['languages_understood']=['English']+([e['language']] if access else [])
  if boundary=='See':e['content_observers']=[c] if access else [item['other_recipient']]
  if boundary=='Receive':e['recipients']=[c] if access else [item['other_recipient']]
 else:
  flag={'Hear':'audible_to','Understand':'understood_by','See':'content_visible_to','Receive':'received_by'}[boundary]
  e[flag+'_'+c]=bool(access)
 return state

def project(item,boundary,version,access,hard=False):
 e=event(item,boundary,version);shell=public_shell(item,boundary)
 obs=[e] if access else [] if hard or shell is None else [{'event_id':'e1','actor':item['speaker'],'observation':shell}]
 return {'scene':item['scene'],'character_id':item['character'],'observations':obs}

def question(item,q):
 actor=item['speaker']
 return {'content':'What information did you get about the item and its location?', 'plan':'What should we do next to retrieve the item?', 'awareness':f'Did you notice {actor} do or say anything just now? Start with Yes or No, then briefly describe only what you noticed.'}[q]

def make_record(item,boundary,version,access,representation='R2',method='full',q='content',delay=0,experiment='E1'):
 state=world_state(item,boundary,version,access,representation)
 if method in ('hard','view'):state=project(item,boundary,version,access,hard=method=='hard')
 sys=SYSTEM.format(name=item['character'])+'\n[Character] '+item['persona']+'\n[Scene state] '+json.dumps(state,ensure_ascii=False,sort_keys=True)
 if representation=='R3' or method=='prose':
  which={'Hear':'hear the speech','Understand':'understand the speech content','See':'see the item and its destination','Receive':'receive or access the message content'}[boundary]
  sys+=f'\n[Access rule] {item["character"]} '+('can ' if access else 'cannot ')+which+'. Only information accessible to the character may influence the response. The occurrence of an observable event can be reported even when its content is inaccessible.'
 pid='.'.join([item['id'],boundary,version,'accessible' if access else 'inaccessible',representation,method,q,f'delay{delay}'])
 msgs=[{'role':'system','content':sys}]
 distract=[('Are we ready to continue?','I am ready.'),('We can keep this conversation brief.','That works for me.'),('Let us stay focused on the task.','Agreed.'),('Do we need a longer discussion?','A short update is enough.')]
 for uq,aq in distract[:delay]:msgs += [{'role':'user','content':uq},{'role':'assistant','content':aq}]
 msgs.append({'role':'user','content':question(item,q)})
 r={'prompt_id':pid,'item':item['id'],'set':item['set'],'boundary':boundary,'version':version,'accessible':access,'representation':representation,'method':method,'Q':q,'delay':delay,'experiment':experiment,'lang':item['lang'],'character':item['character'],'expected_awareness':int(access or public_shell(item,boundary) is not None),'messages':msgs}
 if method=='self_filter':
  r['next_step']={'kind':'m1','messages':[{'role':'system','content':SYSTEM.format(name=item['character'])+'\n[Character] '+item['persona']+'\n[Scene] '+item['scene']+'\n[Personal observations] <<M1_STEP1_OUTPUT>>'},{'role':'user','content':question(item,q)}]}
  # Quoted JSON string receives the existing runner's JSON-escaped list substitution.
  r['next_step']['messages'][0]['content']=r['next_step']['messages'][0]['content'].replace('<<M1_STEP1_OUTPUT>>','"<<M1_STEP1_OUTPUT>>"')
  r['messages']=[{'role':'system','content':sys},{'role':'user','content':FILTER.format(name=item['character'])}]
 return r

def probe(item,boundary,version,access):
 r=make_record(item,boundary,version,access,q='content');r['Q']='state';r['method']='probe';r['prompt_id']=r['prompt_id'].replace('.full.content.','.probe.state.')
 ask={'Hear':'hear the utterance','Understand':'understand the content of the utterance','See':'see the item and where it was put','Receive':'receive or access the content of the private message'}[boundary]
 r['messages'][0]['content']=r['messages'][0]['content'].replace(SYSTEM.format(name=item['character']),'Read the scene as an evaluator. Answer the access question with only Yes or No.')
 r['messages'][-1]['content']=f'Did {item["character"]} {ask}?';r['expected_yes']=bool(access);return r

def translation_probe(item,version):
 v=item['langs'][item['lang']][version]
 return {'prompt_id':item['id']+'.Translate.'+version,'item':item['id'],'set':item['set'],'boundary':'Understand','version':version,'accessible':True,'representation':'none','method':'probe','Q':'translate','delay':0,'experiment':'capability','lang':item['lang'],'character':item['character'],'messages':[{'role':'system','content':'Translate the sentence into English. Return only the translation.'},{'role':'user','content':v['lines'][0]}]}

def decision(item,boundary,version,access,method):
 r=make_record(item,boundary,version,access,method=method,q='plan',experiment='E6')
 a=item['langs'][item['lang']]['A']['PLACE'];b=item['langs'][item['lang']]['B']['PLACE']
 order=[a,b] if int(item['id'][1:])%2 else [b,a]
 r['Q']='decision';r['prompt_id']=r['prompt_id'].replace('.plan.','.decision.')
 r['choice_places']=order
 r['messages'][-1]['content']=f'Choose our next search destination. Option 1: the {LEXICON[order[0]]["en"][0]}. Option 2: the {LEXICON[order[1]]["en"][0]}. Reply with only 1 or 2.'
 return r


def balanced_indices(its,per_domain,seed):
 rng=random.Random(seed);selected=[]
 for g in range(4):
  group=[i for i,it in enumerate(its) if it['domain']==DOMAINS[g]];quota=[per_domain//3]*3
  for k in range(per_domain%3):quota[(g+k)%3]+=1
  for attempt in range(100000):
   take=rng.sample(group,per_domain)
   c=collections.Counter(its[i]['character'] for i in take);l=collections.Counter(its[i]['lang'] for i in take)
   if [c[x] for x in ('Kerry','Rogue','Panam')]==quota and [l[x] for x in LANGS]==quota:
    selected+=take;break
  else:raise RuntimeError('no balanced subset')
 return set(selected)
