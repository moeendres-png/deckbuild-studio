# Tagger-Tag-Zählung gegen die Sammlung — Entscheidungsgrundlage Taxonomie 1.1.0

Stand: 2026-11-12 · Lane `muse/taxonomy-ext-1`

Quelle: offizieller Scryfall-Bulk `oracle_tags`, Datei `oracle-tags-20261112100040.jsonl.gz` (Bulk-Stand 2026-11-12T10:00:40Z, SHA-256 `54fe9777d6a767c8d934966688568ae90cb3547678d9b62212788d468c054ea7`, 6.104.934 Bytes, 4.604 Tags). Sammlungsmenge: 1.324 Oracle-Identitäten mit physischen Lots (DB-Kopie, Integrität geprüft).

Gezählt wurde je Tag seine **Subtree-Vereinigung** (Tag + alle Nachfahren im Tag-Graphen) — exakt die Menge, die ein `function:`-Sync als Claims schreiben würde. `Direkt` = Taggings des Tags selbst, `Global` = Subtree-Größe über alle Karten. Anteil = Sammlungs-Karten / 1.324.

| Tag (Bulk-Key) | Label | Aliase | Sammlung | Anteil % | Direkt | Global |
|---|---|---|---:|---:|---:|---:|
| triggered-ability | triggered ability |  | 530 | 40.03 | 288 | 17516 |
| cycle | cycle |  | 385 | 29.08 | 0 | 8531 |
| activated-ability | activated ability |  | 360 | 27.19 | 312 | 10464 |
| card-names | card names | naming scheme | 300 | 22.66 | 0 | 8761 |
| removal | removal |  | 275 | 20.77 | 0 | 6751 |
| spot-removal | spot removal |  | 255 | 19.26 | 252 | 5629 |
| single-target-instant/sorcery | single target instant/sorcery | single target spell | 242 | 18.28 | 242 | 4731 |
| removal-creature | removal-creature | creature removal | 237 | 17.9 | 63 | 5772 |
| flavors-of-vanilla | flavors of vanilla |  | 218 | 16.47 | 0 | 4599 |
| evasion | evasion |  | 205 | 15.48 | 164 | 5851 |
| card-advantage | card advantage |  | 198 | 14.95 | 0 | 6678 |
| alliteration | alliteration |  | 160 | 12.08 | 160 | 4527 |
| draw | draw |  | 143 | 10.8 | 0 | 4589 |
| burn | burn |  | 135 | 10.2 | 0 | 3216 |
| lifegain | lifegain | life gain | 132 | 9.97 | 51 | 2808 |
| hate | hate |  | 127 | 9.59 | 0 | 4709 |
| pure-draw | pure draw | draw card | 117 | 8.84 | 49 | 3549 |
| removal-burn | removal-burn |  | 112 | 8.46 | 0 | 2536 |
| burn-creature | burn creature | removal-creature-burn | 104 | 7.85 | 39 | 2371 |
| repeatable-crime | repeatable crime |  | 102 | 7.7 | 102 | 3743 |
| removal-planeswalker | removal-planeswalker | planeswalker removal | 96 | 7.25 | 7 | 2077 |
| type-errata | type errata | creature type erratum | 96 | 7.25 | 18 | 2245 |
| burn-player | burn player |  | 89 | 6.72 | 35 | 1953 |
| french-vanilla | french vanilla |  | 82 | 6.19 | 75 | 1627 |
| combat-trick | combat trick |  | 79 | 5.97 | 60 | 1418 |
| ramp | ramp | acceleration;mana ramp | 79 | 5.97 | 10 | 2493 |
| staple-with-set's-mechanic | staple with set's mechanic |  | 79 | 5.97 | 9 | 1704 |
| virtual-vanilla | virtual vanilla |  | 79 | 5.97 | 79 | 1633 |
| single-english-word-name | single english word name |  | 68 | 5.14 | 68 | 1303 |
| unique-type-line | unique type line |  | 66 | 4.98 | 66 | 2500 |
| burn-planeswalker | burn planeswalker | removal-planeswalker-burn | 65 | 4.91 | 13 | 1298 |
| recursion | recursion |  | 65 | 4.91 | 0 | 2368 |
| removal-destroy | removal-destroy |  | 65 | 4.91 | 62 | 1816 |
| typal | typal |  | 65 | 4.91 | 0 | 2954 |
| typal-creature | typal-creature | tribal;kindred | 65 | 4.91 | 0 | 2954 |
| death-trigger | death trigger | deathtrigger | 64 | 4.83 | 19 | 1682 |
| mana-sink | mana sink | mana dump | 63 | 4.76 | 31 | 1930 |
| cheaper-than-mv | cheaper than mv | less expensive than mv | 62 | 4.68 | 40 | 2065 |
| tutor | tutor |  | 59 | 4.46 | 0 | 1235 |
| tutor-to | tutor-to |  | 59 | 4.46 | 0 | 1219 |
| virtual-french-vanilla | virtual french vanilla |  | 59 | 4.46 | 59 | 1348 |
| repeatable-removal | repeatable removal |  | 58 | 4.38 | 57 | 1820 |
| thingfall | thingfall |  | 58 | 4.38 | 0 | 1178 |
| gains-pp-counters | gains pp counters |  | 56 | 4.23 | 52 | 2242 |
| repeatable-card-advantage | repeatable card advantage |  | 56 | 4.23 | 4 | 2953 |
| cycle-land | cycle-land |  | 55 | 4.15 | 0 | 846 |
| type-errata-addition | type errata addition |  | 55 | 4.15 | 0 | 1059 |
| blue-effect | blue effect |  | 54 | 4.08 | 0 | 1498 |
| peek | peek |  | 54 | 4.08 | 0 | 1323 |
| cast-trigger | cast trigger |  | 53 | 4.0 | 4 | 1891 |
| attack-trigger | attack trigger |  | 52 | 3.93 | 47 | 2309 |
| burn-any | burn any |  | 52 | 3.93 | 52 | 914 |
| burn-battle | burn battle | removal-battle-burn | 52 | 3.93 | 0 | 927 |
| mill | mill |  | 52 | 3.93 | 0 | 1378 |
| removal-artifact | removal-artifact | artifact removal | 52 | 3.93 | 10 | 1256 |
| drawback | drawback | own at cost;downside | 51 | 3.85 | 37 | 1848 |
| sacrifice-self | sacrifice self |  | 51 | 3.85 | 12 | 1437 |
| multiple-targets | multiple targets |  | 50 | 3.78 | 50 | 1563 |
| removal-enchantment | removal-enchantment | enchantment removal | 50 | 3.78 | 9 | 1095 |
| library-manipulation | library manipulation |  | 49 | 3.7 | 0 | 1260 |
| repeatable-lifegain | repeatable lifegain |  | 48 | 3.63 | 44 | 1572 |
| mill-self | mill-self | self mill | 47 | 3.55 | 10 | 1130 |
| tapland | tapland |  | 47 | 3.55 | 0 | 518 |
| black-effect | black effect |  | 46 | 3.47 | 0 | 1188 |
| repeatable-draw | repeatable draw |  | 46 | 3.47 | 0 | 2102 |
| gives-mm-counters | gives mm counters |  | 45 | 3.4 | 28 | 237 |
| top-deck-manipulation | top deck manipulation |  | 45 | 3.4 | 0 | 1096 |
| noncreature-typal | noncreature typal | noncreature-tribal | 44 | 3.32 | 44 | 1709 |
| power-boost-to-all | power boost to all |  | 44 | 3.32 | 27 | 1344 |
| more-expensive-than-mv | more expensive than mv | bigger than mv | 43 | 3.25 | 42 | 1082 |
| peek-library | peek-library | spy library | 43 | 3.25 | 2 | 1077 |
| repeatable-pp-counters | repeatable pp counters |  | 42 | 3.17 | 38 | 1846 |
| tutor-land | tutor-land |  | 42 | 3.17 | 0 | 622 |
| utility-land | utility land |  | 42 | 3.17 | 27 | 715 |
| mana-producer | mana producer |  | 40 | 3.02 | 0 | 1012 |
| cast-trigger-you | cast trigger-you |  | 39 | 2.95 | 39 | 1364 |
| draw-engine | draw engine |  | 39 | 2.95 | 39 | 1713 |
| namesake-spell | namesake spell |  | 39 | 2.95 | 39 | 1641 |
| sacrifice-outlet | sacrifice outlet | sac outlet | 39 | 2.95 | 0 | 1554 |
| death-trigger-self | death trigger-self |  | 38 | 2.87 | 30 | 941 |
| gives-evasion | gives evasion |  | 38 | 2.87 | 3 | 1217 |
| protects-self | protects-self |  | 38 | 2.87 | 13 | 1415 |
| additional-cost | additional cost |  | 37 | 2.79 | 36 | 897 |
| attacking-matters-self | attacking matters-self |  | 37 | 2.79 | 37 | 1650 |
| bounce | bounce |  | 37 | 2.79 | 0 | 967 |
| counters-matter | counters matter |  | 37 | 2.79 | 3 | 1357 |
| intervening-if-clause | intervening if clause |  | 37 | 2.79 | 36 | 2273 |
| lands-matter | lands matter | synergy-land | 37 | 2.79 | 0 | 649 |
| cycle-dual-land | cycle-dual-land |  | 36 | 2.72 | 0 | 461 |
| discard-outlet | discard outlet | discardoutlet | 36 | 2.72 | 8 | 1402 |
| dual-land | dual land |  | 36 | 2.72 | 0 | 468 |
| exile-self | exile-self | exiles-self | 36 | 2.72 | 18 | 1419 |
| repeatable-token-generator | repeatable token generator |  | 36 | 2.72 | 0 | 2008 |
| cantrip | cantrip |  | 35 | 2.64 | 35 | 688 |
| power-matters | power matters |  | 35 | 2.64 | 2 | 1625 |
| repeatable-pure-draw | repeatable pure draw |  | 35 | 2.64 | 35 | 1533 |
| gives-pp-counters | gives pp counters |  | 34 | 2.57 | 31 | 1772 |
| opponent-loses-life | opponent loses life |  | 34 | 2.57 | 34 | 919 |
| pinger | pinger | tim | 34 | 2.57 | 34 | 780 |
| removal-toughness | removal-toughness |  | 34 | 2.57 | 34 | 613 |
| protection | protection |  | 33 | 2.49 | 0 | 1280 |
| tutor-to-hand | tutor-to-hand | tutor-hand | 33 | 2.49 | 33 | 638 |
| type-addition-phyrexian | type addition phyrexian |  | 33 | 2.49 | 33 | 231 |
| draft-signpost | draft signpost |  | 32 | 2.42 | 0 | 880 |
| gives-castable-from-nonhand | gives castable from nonhand | cast from nonhand | 32 | 2.42 | 0 | 1076 |
| group-slug | group slug |  | 32 | 2.42 | 30 | 900 |
| synergy-artifact | synergy-artifact | typal-artifact;artifact matters | 32 | 2.42 | 22 | 1124 |
| tutor-land-basic | tutor-land-basic |  | 32 | 2.42 | 29 | 444 |
| alternative-cost | alternative cost | alternate-cost | 31 | 2.34 | 31 | 1330 |
| creaturefall | creaturefall | alliance;etb-other-creature | 31 | 2.34 | 29 | 661 |
| hand-disruption | hand disruption |  | 31 | 2.34 | 0 | 754 |
| saboteur | saboteur |  | 31 | 2.34 | 12 | 1077 |
| bottomless-mana-sink | bottomless mana sink | infinite mana sink | 30 | 2.27 | 30 | 808 |
| discard | discard |  | 30 | 2.27 | 29 | 621 |
| gives-castable-from-exile | gives castable from exile | cast from exile | 30 | 2.27 | 24 | 807 |
| multiple-bodies | multiple bodies |  | 30 | 2.27 | 16 | 950 |
| repeatable-creature-tokens | repeatable creature tokens | repeatable creature token | 30 | 2.27 | 28 | 1562 |
| modal | modal |  | 29 | 2.19 | 11 | 885 |
| removal-equipment | removal-equipment |  | 28 | 2.11 | 2 | 651 |
| type-change | type change |  | 28 | 2.11 | 10 | 1388 |
| protects-creature | protects-creature |  | 27 | 2.04 | 22 | 1007 |
| refund | refund | instant rebate | 27 | 2.04 | 9 | 732 |
| removal-battle | removal-battle |  | 27 | 2.04 | 1 | 641 |
| landfall | landfall |  | 26 | 1.96 | 23 | 308 |
| mana-value-matters | mana value matters | converted mana cost matters;cmc matters | 26 | 1.96 | 5 | 1056 |
| recursion-creature | recursion-creature |  | 26 | 1.96 | 0 | 929 |
| removal-aura | removal-aura |  | 26 | 1.96 | 0 | 653 |
| removal-spacecraft | removal-spacecraft |  | 26 | 1.96 | 0 | 633 |
| removal-vehicle | removal-vehicle |  | 26 | 1.96 | 0 | 641 |
| toughness-boost-to-all | toughness boost to all |  | 26 | 1.96 | 23 | 1023 |
| attacking-matters | attacking matters |  | 25 | 1.89 | 20 | 1284 |
| reanimate | reanimate | zombify;resurrect | 25 | 1.89 | 0 | 1130 |
| repeatable-sacrifice-outlet | repeatable sacrifice outlet | repeatable sac outlet | 25 | 1.89 | 14 | 929 |
| sacrifice-outlet-creature | sacrifice outlet-creature | sac outlet-creature | 25 | 1.89 | 22 | 1032 |
| tapper | tapper |  | 25 | 1.89 | 0 | 749 |
| tapper-creature | tapper-creature | tap creature | 25 | 1.89 | 25 | 702 |
| activate-from-hand | activate from hand |  | 24 | 1.81 | 24 | 585 |
| delayed-trigger | delayed trigger | delayed triggered ability | 24 | 1.81 | 14 | 1327 |
| hate-color | hate-color | color hate | 24 | 1.81 | 0 | 619 |
| removal-bounce | removal-bounce |  | 24 | 1.81 | 19 | 448 |
| surveil | surveil |  | 24 | 1.81 | 17 | 370 |
| tutor-to-battlefield | tutor-to-battlefield | tutor-battlefield;tutor onto battlefield | 24 | 1.81 | 3 | 519 |
| land-ramp | land ramp | rampant growth | 23 | 1.74 | 17 | 675 |
| mana-dork | mana dork |  | 23 | 1.74 | 23 | 464 |
| recursion-self | recursion-self |  | 23 | 1.74 | 0 | 535 |
| regrowth | regrowth | recall | 23 | 1.74 | 0 | 706 |
| activate-from-graveyard | activate from graveyard |  | 22 | 1.66 | 6 | 360 |
| gives-flying | gives flying |  | 22 | 1.66 | 20 | 501 |
| out-of-color-token | out of color token | offcolor token | 22 | 1.66 | 22 | 536 |
| remove-counters | remove counters | remove counter | 22 | 1.66 | 0 | 586 |
| remove-counters-you | remove counters-you |  | 22 | 1.66 | 1 | 580 |
| tap-outlet | tap outlet |  | 22 | 1.66 | 0 | 1020 |
| burst-draw | burst draw |  | 21 | 1.59 | 20 | 683 |
| inverted-effects | inverted effects |  | 21 | 1.59 | 2 | 542 |
| self-replacement-effect | self-replacement effect |  | 21 | 1.59 | 21 | 378 |
| tutor-land-to-battlefield | tutor-land-to-battlefield |  | 21 | 1.59 | 15 | 340 |
| castable-from-graveyard | castable from graveyard | flashback | 20 | 1.51 | 20 | 418 |
| castable-from-nonhand | castable from nonhand |  | 20 | 1.51 | 0 | 914 |
| control-changing-effects | control changing effects |  | 20 | 1.51 | 0 | 879 |
| counterspell | counterspell | counter | 20 | 1.51 | 4 | 566 |
| discount-self | discount-self | cost-reducer-self | 20 | 1.51 | 9 | 591 |
| multi-removal | multi removal |  | 20 | 1.51 | 20 | 685 |
| synergy-instant | synergy-instant |  | 20 | 1.51 | 17 | 587 |
| synergy-sorcery | synergy-sorcery |  | 20 | 1.51 | 17 | 584 |
| tap-fuel-creature | tap fuel-creature |  | 20 | 1.51 | 9 | 794 |
| bottom-deck-manipulation | bottom deck manipulation |  | 19 | 1.44 | 4 | 704 |
| burn-with-set's-mechanic | burn with set's mechanic | burn with set mechanic | 19 | 1.44 | 19 | 299 |
| drain-life | drain life | life drain | 19 | 1.44 | 17 | 439 |
| giant-growth | giant growth |  | 19 | 1.44 | 12 | 311 |
| red-effect | red effect |  | 19 | 1.44 | 0 | 686 |
| removal-exile | removal-exile |  | 19 | 1.44 | 16 | 617 |
| sweeper | sweeper | wipe;boardwipe;wrath of god;mass removal | 19 | 1.44 | 10 | 994 |
| cards-in-graveyard-matter | cards in graveyard matter |  | 18 | 1.36 | 8 | 675 |
| impulse | impulse |  | 18 | 1.36 | 2 | 607 |
| poison-mechanics | poison mechanics |  | 18 | 1.36 | 0 | 198 |
| removal-nonland | removal-nonland |  | 18 | 1.36 | 18 | 400 |
| rescue | rescue |  | 18 | 1.36 | 1 | 390 |
| untapper | untapper |  | 18 | 1.36 | 0 | 805 |
| characteristic-defining-ability | characteristic-defining ability | cda | 17 | 1.28 | 0 | 489 |
| counter-fuel | counter fuel |  | 17 | 1.28 | 0 | 517 |
| martyr | martyr |  | 17 | 1.28 | 15 | 593 |
| mini-refund | mini refund |  | 17 | 1.28 | 17 | 353 |
| scales-with-power | scales with power |  | 17 | 1.28 | 9 | 705 |
| theft | theft |  | 17 | 1.28 | 1 | 791 |
| adds-multiple-mana | adds multiple mana | produces multiple mana | 16 | 1.21 | 15 | 548 |
| cost-ignorer | cost ignorer | cheat mana | 16 | 1.21 | 2 | 1048 |
| enlarge | enlarge |  | 16 | 1.21 | 16 | 316 |
| gains-flying | gains flying |  | 16 | 1.21 | 16 | 389 |
| mana-rock | mana rock | manarock-chosen-color;manarock-any-color;manarock-ccc;manarock-c;manarock-cc;manarock | 16 | 1.21 | 6 | 404 |
| removal-land | removal-land | land removal | 16 | 1.21 | 8 | 532 |
| symmetrical | symmetrical |  | 16 | 1.21 | 15 | 939 |
| untapper-creature | untapper-creature | untap creature | 16 | 1.21 | 15 | 549 |
| anthem | anthem | lord | 15 | 1.13 | 15 | 580 |
| copy | copy |  | 15 | 1.13 | 0 | 1125 |
| disenchant/naturalize | disenchant/naturalize | disenchant;naturalize | 15 | 1.13 | 12 | 250 |
| egg | egg |  | 15 | 1.13 | 15 | 384 |
| mm-counter-cost | mm counter cost |  | 15 | 1.13 | 15 | 43 |
| poisonous | poisonous |  | 15 | 1.13 | 15 | 132 |
| prevent-blocker | prevent blocker |  | 15 | 1.13 | 14 | 317 |
| scry | scry |  | 15 | 1.13 | 13 | 483 |
| unique-mana-cost | unique mana cost |  | 15 | 1.13 | 15 | 328 |
| block-trigger | block trigger |  | 14 | 1.06 | 14 | 421 |
| cda-subtype | cda-subtype |  | 14 | 1.06 | 0 | 81 |
| changeling | changeling |  | 14 | 1.06 | 14 | 73 |
| color-change | color change |  | 14 | 1.06 | 11 | 261 |
| enters-in-company | enters in company |  | 14 | 1.06 | 14 | 512 |
| fun-ruling | fun ruling | funny ruling | 14 | 1.06 | 14 | 381 |
| gives-haste | gives haste |  | 14 | 1.06 | 14 | 728 |
| hate-set-mechanic | hate-set-mechanic |  | 14 | 1.06 | 14 | 277 |
| life-payment | life payment |  | 14 | 1.06 | 4 | 834 |
| regrowth-creature | regrowth-creature |  | 14 | 1.06 | 14 | 346 |
| synergy-white | synergy-white |  | 14 | 1.06 | 14 | 214 |
| bear-with-set's-mechanic | bear with set's mechanic | bear with set mechanic | 13 | 0.98 | 13 | 303 |
| cycle-mono-land | cycle-mono-land |  | 13 | 0.98 | 0 | 244 |
| damage-prevention | damage prevention | prevent damage | 13 | 0.98 | 8 | 615 |
| firebreathing | firebreathing |  | 13 | 0.98 | 13 | 299 |
| gainland | gainland |  | 13 | 0.98 | 1 | 54 |
| gains-haste | gains haste |  | 13 | 0.98 | 4 | 353 |
| gives-trample | gives trample |  | 13 | 0.98 | 10 | 545 |
| lifegain-matters | lifegain matters | synergy-lifegain | 13 | 0.98 | 6 | 251 |
| removal-sacrifice | removal-sacrifice | edict | 13 | 0.98 | 8 | 460 |
| rescue-creature | rescue-creature |  | 13 | 0.98 | 5 | 284 |
| type-addition-human | type addition human |  | 13 | 0.98 | 13 | 573 |
| animate | animate |  | 12 | 0.91 | 0 | 687 |
| curiosity-like | curiosity-like |  | 12 | 0.91 | 1 | 376 |
| freeze | freeze | stun | 12 | 0.91 | 0 | 214 |
| hate-graveyard | hate-graveyard | graveyard hate | 12 | 0.91 | 7 | 449 |
| jump | jump |  | 12 | 0.91 | 12 | 224 |
| land-count-matters | land count matters |  | 12 | 0.91 | 8 | 285 |
| loot | loot |  | 12 | 0.91 | 4 | 443 |
| offcolor-ability | offcolor ability |  | 12 | 0.91 | 12 | 340 |
| reanimate-self | reanimate-self | self reanimate | 12 | 0.91 | 3 | 277 |
| shade-pump | shade pump |  | 12 | 0.91 | 12 | 300 |
| type-errata-summon-creature | type errata summon creature |  | 12 | 0.91 | 12 | 100 |
| curiosity | curiosity |  | 11 | 0.83 | 11 | 261 |
| freeze-creature | freeze-creature | stun-creature | 11 | 0.83 | 11 | 194 |
| gains-mm-counters | gains mm counters |  | 11 | 0.83 | 11 | 76 |
| hate-attacker | hate-attacker |  | 11 | 0.83 | 11 | 378 |
| mill-opponent | mill-opponent | deck destruction | 11 | 0.83 | 4 | 482 |
| peek-hand | peek-hand |  | 11 | 0.83 | 2 | 245 |
| reanimate-creature | reanimate-creature |  | 11 | 0.83 | 11 | 565 |
| aikido | aikido |  | 10 | 0.76 | 10 | 176 |
| charm | charm | modal-1/3 | 10 | 0.76 | 2 | 123 |
| combat-manipulation | combat manipulation |  | 10 | 0.76 | 0 | 327 |
| cycle-guildgate | cycle-guildgate |  | 10 | 0.76 | 10 | 10 |
| cycle-ktk-gainland | cycle-ktk-gainland | cycle-gainland | 10 | 0.76 | 10 | 10 |
| finality | finality |  | 10 | 0.76 | 0 | 152 |
| hate-artifact | hate-artifact |  | 10 | 0.76 | 10 | 205 |
| hate-flying | hate-flying | flying hate | 10 | 0.76 | 9 | 211 |
| impulse-creature | impulse-creature |  | 10 | 0.76 | 10 | 189 |
| life-for-cards | life for cards |  | 10 | 0.76 | 10 | 329 |
| prevent-attack | prevent attack | prevent attacker | 10 | 0.76 | 9 | 170 |
| restock | restock | graveyard to library | 10 | 0.76 | 0 | 237 |
| rummage | rummage |  | 10 | 0.76 | 5 | 297 |
| sacrifice-outlet-artifact | sacrifice outlet-artifact | sac outlet-artifact | 10 | 0.76 | 9 | 372 |
| single-minded-hate | single-minded hate |  | 10 | 0.76 | 0 | 202 |
| synergy-blocker-self | synergy-blocker-self |  | 10 | 0.76 | 10 | 212 |
| synergy-noncreature | synergy-noncreature |  | 10 | 0.76 | 10 | 340 |
| tax | tax |  | 10 | 0.76 | 0 | 490 |
| artifact-count-matters | artifact count matters |  | 9 | 0.68 | 1 | 191 |
| cheat-death | cheat death | graveflicker;creature-reanimation-automatic | 9 | 0.68 | 4 | 322 |
| cycle-block-ths-scry-land | cycle-block-ths-scry-land | cycle-scryland;cycle-scry-land;cycle-temple-land | 9 | 0.68 | 9 | 10 |
| cycle-ecl-c-hybrid | cycle-ecl-c-hybrid |  | 9 | 0.68 | 4 | 10 |
| force-draw | force draw | opponent draw | 9 | 0.68 | 9 | 333 |
| free-cast-another | free-cast-another | free casting | 9 | 0.68 | 9 | 437 |
| gives-first-strike | gives first strike |  | 9 | 0.68 | 9 | 290 |
| gives-lifelink | gives lifelink |  | 9 | 0.68 | 9 | 237 |
| hate-white | hate-white | white hate | 9 | 0.68 | 9 | 121 |
| high-mana-value-matters | high mana value matters | high mv matters | 9 | 0.68 | 9 | 80 |
| humble | humble |  | 9 | 0.68 | 9 | 140 |
| keyword-anthem | keyword anthem |  | 9 | 0.68 | 9 | 531 |
| pp-counters-matter | pp counters matter |  | 9 | 0.68 | 8 | 457 |
| rescue-artifact | rescue-artifact |  | 9 | 0.68 | 1 | 87 |
| single-minded-color-hate | single-minded color hate | single-minded hate-color | 9 | 0.68 | 9 | 130 |
| sweeper-one-sided | sweeper-one-sided |  | 9 | 0.68 | 9 | 249 |
| synergy-color-each | synergy-color-each |  | 9 | 0.68 | 1 | 65 |
| synergy-color-share | synergy-color-share |  | 9 | 0.68 | 1 | 161 |
| temporary-reanimation | temporary reanimation |  | 9 | 0.68 | 0 | 103 |
| thoughtseize | thoughtseize | coercion;duress | 9 | 0.68 | 9 | 160 |
| typal-elf | typal-elf | tribal-elf | 9 | 0.68 | 9 | 132 |
| unearth | unearth |  | 9 | 0.68 | 9 | 58 |
| aesthetic-counter | aesthetic counter |  | 8 | 0.6 | 7 | 351 |
| animate-self | animate self | becomes creature | 8 | 0.6 | 3 | 435 |
| consult | consult |  | 8 | 0.6 | 1 | 253 |
| convoke | convoke | discount-tap-creature;alternate-cost-tap-creature | 8 | 0.6 | 8 | 112 |
| creature-count-matters | creature count matters |  | 8 | 0.6 | 8 | 340 |
| drain-creature | drain creature |  | 8 | 0.6 | 8 | 97 |
| free-sacrifice-outlet | free sacrifice outlet | free-sac-outlet | 8 | 0.6 | 8 | 192 |
| gains-trample | gains trample |  | 8 | 0.6 | 8 | 256 |
| gives-hexproof | gives hexproof |  | 8 | 0.6 | 8 | 173 |
| gives-indestructible | gives indestructible |  | 8 | 0.6 | 8 | 288 |
| green-effect | green effect |  | 8 | 0.6 | 0 | 209 |
| hate-blocker | hate-blocker |  | 8 | 0.6 | 7 | 458 |
| hate-target | hate-target |  | 8 | 0.6 | 0 | 323 |
| multiplayer | multiplayer |  | 8 | 0.6 | 0 | 670 |
| name-matters | name matters |  | 8 | 0.6 | 3 | 534 |
| per-player | per-player | per-opponent | 8 | 0.6 | 7 | 506 |
| power-matters-individual | power matters-individual |  | 8 | 0.6 | 3 | 202 |
| protects-all | protects-all |  | 8 | 0.6 | 8 | 307 |
| punny-name | punny name |  | 8 | 0.6 | 8 | 523 |
| rescue-enchantment | rescue-enchantment |  | 8 | 0.6 | 0 | 83 |
| scales-with-mana-value | scales with mana value | scales with mv | 8 | 0.6 | 8 | 385 |
| synergy-planeswalker | synergy-planeswalker | typal-planeswalker;planeswalker support | 8 | 0.6 | 7 | 265 |
| typal-kithkin | typal-kithkin | kithkin tribal;tribal-kithkin | 8 | 0.6 | 8 | 28 |
| uninspired | uninspired |  | 8 | 0.6 | 8 | 156 |
| vivid | vivid |  | 8 | 0.6 | 8 | 32 |
| ward | ward |  | 8 | 0.6 | 4 | 221 |
| cast-trigger-self | cast trigger-self |  | 7 | 0.53 | 7 | 254 |
| consult-cast | consult-cast |  | 7 | 0.53 | 7 | 136 |
| copy-creature | copy-creature |  | 7 | 0.53 | 7 | 414 |
| cost-reducer | cost reducer |  | 7 | 0.53 | 1 | 389 |
| cycle-fdn-draft-signpost | cycle-fdn-draft-signpost |  | 7 | 0.53 | 7 | 10 |
| eponymous | eponymous | name-type | 7 | 0.53 | 7 | 92 |
| french-vanilla-walker | french vanilla walker |  | 7 | 0.53 | 7 | 68 |
| giant-growth-with-set-mechanic | giant growth with set mechanic | giant growth with set's mechanic | 7 | 0.53 | 7 | 142 |
| gives-deathtouch | gives deathtouch |  | 7 | 0.53 | 7 | 191 |
| graveyard-fuel-self | graveyard fuel-self |  | 7 | 0.53 | 0 | 196 |
| group-hug | group hug |  | 7 | 0.53 | 4 | 447 |
| hate-blue | hate-blue | blue hate | 7 | 0.53 | 7 | 97 |
| mana-filter | mana filter |  | 7 | 0.53 | 6 | 233 |
| mana-rock-with-set's-mechanic | mana rock with set's mechanic |  | 7 | 0.53 | 7 | 105 |
| mana-spent-matters | mana spent matters |  | 7 | 0.53 | 0 | 223 |
| meme | meme |  | 7 | 0.53 | 7 | 130 |
| metalcraft | metalcraft |  | 7 | 0.53 | 7 | 43 |
| mulch | mulch |  | 7 | 0.53 | 7 | 181 |
| pacifism | pacifism | arrest | 7 | 0.53 | 7 | 96 |
| power-matters-self | power matters-self |  | 7 | 0.53 | 6 | 314 |
| regrowth-self | regrowth-self | self regrowth;self recall | 7 | 0.53 | 7 | 200 |
| removal-permanent | removal-permanent |  | 7 | 0.53 | 7 | 214 |
| renew | renew |  | 7 | 0.53 | 7 | 163 |
| repeatable-artifact-tokens | repeatable artifact tokens |  | 7 | 0.53 | 4 | 635 |
| repeatable-surveil | repeatable surveil |  | 7 | 0.53 | 7 | 159 |
| shrink | shrink |  | 7 | 0.53 | 5 | 170 |
| theft-creature | theft-creature |  | 7 | 0.53 | 7 | 246 |
| trumpet-blast | trumpet blast | burn bright | 7 | 0.53 | 5 | 57 |
| tuck | tuck |  | 7 | 0.53 | 0 | 228 |
| type-errata-genericise | type errata genericise |  | 7 | 0.53 | 0 | 222 |
| utility-mana-rock | utility mana rock |  | 7 | 0.53 | 7 | 252 |
| bounce-self | bounce-self |  | 6 | 0.45 | 5 | 219 |
| color-break | color break |  | 6 | 0.45 | 6 | 160 |
| copy-spell | copy-spell |  | 6 | 0.45 | 5 | 212 |
| counter-fuel-charge | counter fuel-charge |  | 6 | 0.45 | 6 | 65 |
| cycle-ecl-draft-signpost | cycle-ecl-draft-signpost |  | 6 | 0.45 | 0 | 10 |
| discard-with-set's-mechanic | discard with set's mechanic |  | 6 | 0.45 | 6 | 204 |
| extra-land | extra land |  | 6 | 0.45 | 0 | 178 |
| fetchland | fetchland |  | 6 | 0.45 | 4 | 56 |
| force-blocker | force blocker |  | 6 | 0.45 | 1 | 138 |
| french-vanilla-aura | french vanilla aura |  | 6 | 0.45 | 6 | 110 |
| gains-deathtouch | gains deathtouch |  | 6 | 0.45 | 6 | 123 |
| hate-black | hate-black | black hate | 6 | 0.45 | 6 | 156 |
| hate-counterspell | hate-counterspell |  | 6 | 0.45 | 3 | 159 |
| hate-red | hate-red | red hate | 6 | 0.45 | 6 | 133 |
| hate-regenerate | hate-regenerate | hate-regeneration;stops regeneration;prevent regeneration | 6 | 0.45 | 6 | 141 |
| hate-typal | hate-typal | tribal hate | 6 | 0.45 | 0 | 281 |
| impulsive-draw | impulsive draw | impulse draw;bottle draw | 6 | 0.45 | 0 | 277 |
| leaves-battlefield-trigger | leaves battlefield trigger | leaves trigger | 6 | 0.45 | 1 | 242 |
| long-term-impulsive-draw | long term impulsive draw |  | 6 | 0.45 | 6 | 119 |
| mill-any | mill-any |  | 6 | 0.45 | 6 | 190 |
| mm-counters-matter | mm counters matter |  | 6 | 0.45 | 1 | 59 |
| multi-land-ramp | multi land ramp | explosive vegetation;mass land ramp | 6 | 0.45 | 6 | 173 |
| portmanteau | portmanteau |  | 6 | 0.45 | 6 | 148 |
| quick-attach | quick attach |  | 6 | 0.45 | 0 | 269 |
| quick-equip | quick equip |  | 6 | 0.45 | 0 | 253 |
| reflexive-trigger | reflexive trigger |  | 6 | 0.45 | 6 | 315 |
| regenerates-self | regenerates self |  | 6 | 0.45 | 6 | 200 |
| removal-fight | removal-fight | fight;removal-creature-fight | 6 | 0.45 | 6 | 155 |
| repeatable-noncreature-tokens | repeatable noncreature tokens |  | 6 | 0.45 | 3 | 486 |
| rescue-land | rescue-land |  | 6 | 0.45 | 2 | 123 |
| sacrifice-outlet-land | sacrifice outlet-land | land sacrifice;sac outlet-land | 6 | 0.45 | 5 | 294 |
| synergy-red | synergy-red |  | 6 | 0.45 | 6 | 189 |
| token-errata | token errata |  | 6 | 0.45 | 6 | 61 |
| type-addition-from-none | type addition from none |  | 6 | 0.45 | 6 | 161 |
| unblockable | unblockable |  | 6 | 0.45 | 6 | 243 |
| behold | behold |  | 5 | 0.38 | 1 | 38 |
| bombard | bombard |  | 5 | 0.38 | 5 | 115 |
| cost-reducer-creature | cost-reducer-creature |  | 5 | 0.38 | 5 | 87 |
| counter-fuel-any | counter fuel-any |  | 5 | 0.38 | 5 | 38 |
| counterspell-soft | counterspell-soft | soft counter | 5 | 0.38 | 4 | 143 |
| cycle-ecl-c-hybrid-changeling | cycle-ecl-c-hybrid-changeling |  | 5 | 0.38 | 5 | 5 |
| cycle-fdn-enemy-hate | cycle-fdn-enemy-hate |  | 5 | 0.38 | 5 | 5 |
| cycle-fra-c-hybrid | cycle-fra-c-hybrid |  | 5 | 0.38 | 5 | 10 |
| cycle-lea-basic-land | cycle-lea-basic-land |  | 5 | 0.38 | 5 | 6 |
| cycle-m11-enemy-hate | cycle-m11-enemy-hate |  | 5 | 0.38 | 5 | 5 |
| cycle-spm-c-legend | cycle-spm-c-legend |  | 5 | 0.38 | 5 | 10 |
| cycle-wwk-landfall-instant | cycle-wwk-landfall-instant |  | 5 | 0.38 | 5 | 5 |
| damage-prevention-self | damage prevention-self |  | 5 | 0.38 | 5 | 141 |
| discard-matters | discard matters | synergy-discard | 5 | 0.38 | 0 | 211 |
| exalted | exalted |  | 5 | 0.38 | 5 | 48 |
| french-vanilla-equipment | french vanilla equipment |  | 5 | 0.38 | 5 | 55 |
| gains-first-strike | gains first strike |  | 5 | 0.38 | 5 | 206 |
| gains-vigilance | gains vigilance |  | 5 | 0.38 | 5 | 150 |
| gives-protection | gives protection |  | 5 | 0.38 | 5 | 128 |
| graveyard-fuel | graveyard fuel |  | 5 | 0.38 | 1 | 482 |
| hand-size-matters | hand size matters | high hand size matters;handsize matters;low hand size matters | 5 | 0.38 | 1 | 300 |
| has-identical-token | has identical token |  | 5 | 0.38 | 5 | 39 |
| hate-high-mv | hate-high-mv | hate-high-mana-value;hate-high-cmc | 5 | 0.38 | 5 | 93 |
| impulse-land | impulse-land |  | 5 | 0.38 | 5 | 106 |
| indefinite-effect | indefinite effect | permanent effect | 5 | 0.38 | 0 | 510 |
| leaves-trigger-self | leaves trigger-self |  | 5 | 0.38 | 5 | 174 |
| man-o'-war | man-o'-war |  | 5 | 0.38 | 5 | 101 |
| plunder | plunder |  | 5 | 0.38 | 2 | 220 |
| prevent-activation | prevent activation |  | 5 | 0.38 | 4 | 91 |
| pseudo-fog | pseudo-fog |  | 5 | 0.38 | 5 | 77 |
| raid | raid |  | 5 | 0.38 | 5 | 49 |
| ramp-with-set's-mechanic | ramp with set's mechanic | ramp with set mechanic | 5 | 0.38 | 5 | 78 |
| real-life-animal-name | real life animal name |  | 5 | 0.38 | 5 | 139 |
| removes-mm-counters | removes-mm-counters | heartmend | 5 | 0.38 | 0 | 31 |
| removes-mm-counters-self | removes-mm-counters-self |  | 5 | 0.38 | 5 | 23 |
| repeatable-loot | repeatable loot |  | 5 | 0.38 | 5 | 255 |
| rescue-nonland | rescue-nonland |  | 5 | 0.38 | 5 | 36 |
| rhystic | rhystic |  | 5 | 0.38 | 5 | 266 |
| self-discard-matters | self-discard matters | synergy-discard-self | 5 | 0.38 | 5 | 175 |
| shapechange | shapechange |  | 5 | 0.38 | 5 | 258 |
| synergy-blue | synergy-blue |  | 5 | 0.38 | 5 | 168 |
| synergy-forest | synergy-forest |  | 5 | 0.38 | 5 | 128 |
| synergy-gate | synergy-gate |  | 5 | 0.38 | 3 | 35 |
| synergy-green | synergy-green |  | 5 | 0.38 | 5 | 199 |
| synergy-island | synergy-island |  | 5 | 0.38 | 5 | 91 |
| synergy-multicolor | synergy-multicolor | synergy-color-multi | 5 | 0.38 | 4 | 94 |
| synergy-solo-attack | synergy-solo-attack |  | 5 | 0.38 | 0 | 105 |
| threaten | threaten | theft-threaten | 5 | 0.38 | 3 | 137 |
| token-versions-of-cards | token versions of cards |  | 5 | 0.38 | 0 | 144 |
| toll | toll |  | 5 | 0.38 | 5 | 219 |
| tome | tome |  | 5 | 0.38 | 5 | 162 |
| toughness-matters | toughness matters |  | 5 | 0.38 | 4 | 216 |
| trigger-from-graveyard | trigger from graveyard |  | 5 | 0.38 | 5 | 147 |
| tutor-card | tutor-card | tutor-any;demonic tutor | 5 | 0.38 | 5 | 113 |
| typal-ally | typal-ally | tribal-ally | 5 | 0.38 | 5 | 85 |
| typal-vampire | typal-vampire | tribal-vampire;vampire lord | 5 | 0.38 | 5 | 84 |
| unnoted-tracked-information | unnoted tracked information |  | 5 | 0.38 | 5 | 257 |
| untracked-indefinite-effect | untracked indefinite effect | permanent p/t boost | 5 | 0.38 | 5 | 497 |
| animate-land | animate land |  | 4 | 0.3 | 4 | 156 |
| ball-lightning | ball lightning |  | 4 | 0.3 | 4 | 46 |
| battle-cry | battle cry |  | 4 | 0.3 | 4 | 20 |
| bombard-self | bombard-self |  | 4 | 0.3 | 4 | 145 |
| burn-you | burn-you |  | 4 | 0.3 | 2 | 278 |
| cheat-death-self | cheat death-self |  | 4 | 0.3 | 4 | 158 |
| class-type-only | class type only |  | 4 | 0.3 | 4 | 73 |
| color-spent-matters | color spent matters |  | 4 | 0.3 | 4 | 116 |
| copy-instant | copy-instant |  | 4 | 0.3 | 4 | 163 |
| copy-sorcery | copy-sorcery |  | 4 | 0.3 | 4 | 158 |
| counter-fuel-aesthetic | counter fuel-aesthetic |  | 4 | 0.3 | 4 | 152 |
| counterspell-with-set-mechanic | counterspell with set mechanic | counterspell with set's mechanic | 4 | 0.3 | 4 | 169 |
| counterspell-noncreature | counterspell-noncreature |  | 4 | 0.3 | 4 | 37 |
| creates-bigger-body | creates bigger body | creates larger body;say hello to my little friend | 4 | 0.3 | 4 | 226 |
| creature-engine | creature engine |  | 4 | 0.3 | 4 | 91 |
| cycle-arb-c-cascade | cycle-arb-c-cascade |  | 4 | 0.3 | 4 | 5 |
| cycle-arb-dual-landcycler | cycle-arb-dual-landcycler |  | 4 | 0.3 | 4 | 5 |
| cycle-ecl-u-changeling | cycle-ecl-u-changeling |  | 4 | 0.3 | 4 | 5 |
| cycle-fra-draft-signpost | cycle-fra-draft-signpost |  | 4 | 0.3 | 4 | 10 |
| cycle-fra-wedge-pair | cycle-fra-wedge-pair |  | 4 | 0.3 | 4 | 10 |
| cycle-m10-enemy-hate | cycle-m10-enemy-hate |  | 4 | 0.3 | 4 | 5 |
| cycle-mm2-enemy-hate | cycle-mm2-enemy-hate |  | 4 | 0.3 | 4 | 5 |
| cycle-mrd-mana-myr | cycle-mrd-mana-myr |  | 4 | 0.3 | 4 | 5 |
| cycle-sos-charm | cycle-sos-charm |  | 4 | 0.3 | 4 | 5 |
| discard-outlet-land | discard outlet-land |  | 4 | 0.3 | 4 | 52 |
| ditch-hand | ditch hand |  | 4 | 0.3 | 2 | 242 |
| flowstone | flowstone |  | 4 | 0.3 | 4 | 117 |
| force-attacker | force attacker | forces attack | 4 | 0.3 | 4 | 172 |
| forced-attacker | forced attacker |  | 4 | 0.3 | 4 | 89 |
| gains-indestructible | gains indestructible |  | 4 | 0.3 | 4 | 166 |
| gives-unblockable | gives unblockable |  | 4 | 0.3 | 2 | 200 |
| graveyard-fuel-creature | graveyard fuel-creature |  | 4 | 0.3 | 4 | 183 |
| hand-size-hate | hand size hate |  | 4 | 0.3 | 0 | 98 |
| hate-discard | hate-discard |  | 4 | 0.3 | 4 | 137 |
| hate-high-pt | hate-high-pt |  | 4 | 0.3 | 4 | 195 |
| illusion-ability | illusion ability |  | 4 | 0.3 | 4 | 32 |
| leaves-body-behind | leaves body behind | afterlife;doomed traveler | 4 | 0.3 | 4 | 168 |
| life-and-death-trigger-self | life-and-death-trigger-self | enters-and-dies-trigger-self | 4 | 0.3 | 4 | 36 |
| living-weapon | living weapon |  | 4 | 0.3 | 4 | 86 |
| low-mana-value-matters | low mana value matters | low mv matters | 4 | 0.3 | 4 | 235 |
| modal-inverse-choices | modal inverse choices |  | 4 | 0.3 | 4 | 92 |
| mutual-sacrifice | mutual sacrifice | mutual edict | 4 | 0.3 | 3 | 78 |
| non-mana-ward | non-mana ward |  | 4 | 0.3 | 4 | 56 |
| pridemate | pridemate |  | 4 | 0.3 | 3 | 59 |
| prowess-like | prowess-like |  | 4 | 0.3 | 4 | 84 |
| quest | quest |  | 4 | 0.3 | 4 | 74 |
| recursion-land | recursion-land |  | 4 | 0.3 | 0 | 119 |
| removal-tuck | removal-tuck |  | 4 | 0.3 | 4 | 151 |
| repeatable-proliferate | repeatable proliferate |  | 4 | 0.3 | 4 | 71 |
| restock-self | restock-self | self restock | 4 | 0.3 | 3 | 61 |
| restock-to-top | restock-to-top |  | 4 | 0.3 | 4 | 67 |
| slith-ability | slith ability | bloodlust | 4 | 0.3 | 4 | 69 |
| sneak | sneak | cheat into play | 4 | 0.3 | 0 | 297 |
| specter-ability | specter ability |  | 4 | 0.3 | 4 | 63 |
| swap-removal | swap removal | beast within;pongify | 4 | 0.3 | 4 | 136 |
| synergy-burn | synergy-burn |  | 4 | 0.3 | 4 | 66 |
| synergy-plains | synergy-plains |  | 4 | 0.3 | 4 | 66 |
| tapper-artifact | tapper-artifact | tap artifact | 4 | 0.3 | 4 | 139 |
| threshold | threshold |  | 4 | 0.3 | 4 | 120 |
| titan-trigger | titan trigger |  | 4 | 0.3 | 4 | 180 |
| tmp-storyline-in-cards | tmp-storyline-in-cards |  | 4 | 0.3 | 4 | 60 |
| tutor-artifact | tutor-artifact |  | 4 | 0.3 | 3 | 78 |
| tutor-mv | tutor-mv | tutor-cmc | 4 | 0.3 | 2 | 108 |
| typal-goblin | typal-goblin | tribal-goblin;goblin synergy | 4 | 0.3 | 4 | 131 |
| typal-spider | typal-spider | tribal-spider | 4 | 0.3 | 4 | 30 |
| type-errata-specific | type errata specific |  | 4 | 0.3 | 0 | 99 |
| untapper-land | untapper-land | untap land | 4 | 0.3 | 3 | 180 |
| usg-storyline-in-cards | usg-storyline-in-cards |  | 4 | 0.3 | 4 | 63 |
| vertical-cycle | vertical-cycle |  | 4 | 0.3 | 0 | 158 |
| virtual-legendary | virtual legendary |  | 4 | 0.3 | 4 | 220 |
| affinity | affinity |  | 3 | 0.23 | 0 | 140 |
| amount-spent-matters | amount spent matters |  | 3 | 0.23 | 3 | 109 |
| banish | banish | o-ring;oblivion ring effect | 3 | 0.23 | 3 | 161 |
| cast-trigger-other | cast trigger-other |  | 3 | 0.23 | 3 | 131 |
| casting-restriction | casting restriction |  | 3 | 0.23 | 1 | 69 |
| cda-power | cda-power |  | 3 | 0.23 | 3 | 256 |
| color-change-self | color change-self |  | 3 | 0.23 | 3 | 90 |
| combat-ramp | combat ramp | combat mana | 3 | 0.23 | 2 | 210 |
| counterspell-creature | counterspell-creature |  | 3 | 0.23 | 3 | 51 |
| crew | crew | crewed vehicle | 3 | 0.23 | 3 | 199 |
| cycle-ala-c-1-drop | cycle-ala-c-1-drop |  | 3 | 0.23 | 3 | 5 |
| cycle-ala-esper-capsule | cycle-ala-esper-capsule |  | 3 | 0.23 | 3 | 3 |
| cycle-ala-shard-ultimatum | cycle-ala-shard-ultimatum |  | 3 | 0.23 | 3 | 5 |
| cycle-ala-u-two-color | cycle-ala-u-two-color |  | 3 | 0.23 | 3 | 10 |
| cycle-arb-shard-blade | cycle-arb-shard-blade |  | 3 | 0.23 | 3 | 5 |
| cycle-colorless-land | cycle-colorless-land |  | 3 | 0.23 | 0 | 49 |
| cycle-dst-lucky-charm | cycle-dst-lucky-charm |  | 3 | 0.23 | 3 | 6 |
| cycle-ecl-hybrid-signpost | cycle-ecl-hybrid-signpost |  | 3 | 0.23 | 3 | 5 |
| cycle-ecl-typal-signpost | cycle-ecl-typal-signpost |  | 3 | 0.23 | 3 | 5 |
| cycle-ecl-u-behold | cycle-ecl-u-behold |  | 3 | 0.23 | 3 | 5 |
| cycle-m11-c-pw-signature | cycle-m11-c-pw-signature |  | 3 | 0.23 | 3 | 5 |
| cycle-m12-c-pw-signature | cycle-m12-c-pw-signature |  | 3 | 0.23 | 3 | 5 |
| cycle-mbs-color-artifact | cycle-mbs-color-artifact |  | 3 | 0.23 | 3 | 5 |
| cycle-mm3-draft-signpost | cycle-mm3-draft-signpost |  | 3 | 0.23 | 3 | 25 |
| cycle-som-replica | cycle-som-replica |  | 3 | 0.23 | 3 | 5 |
| cycle-spellshaped-from-fut | cycle-spellshaped-from-fut |  | 3 | 0.23 | 3 | 6 |
| cycle-spm-color-coded-artifact | cycle-spm-color-coded-artifact |  | 3 | 0.23 | 3 | 5 |
| cycle-spm-u-hybrid | cycle-spm-u-hybrid |  | 3 | 0.23 | 3 | 5 |
| cycle-w16-u | cycle-w16-u |  | 3 | 0.23 | 3 | 5 |
| cycle-wwk-allied-land-bonus | cycle-wwk-allied-land-bonus |  | 3 | 0.23 | 3 | 5 |
| cycle-wwk-c-multikicker | cycle-wwk-c-multikicker |  | 3 | 0.23 | 3 | 5 |
| cycle-wwk-enemy-hate-trap | cycle-wwk-enemy-hate-trap |  | 3 | 0.23 | 3 | 5 |
| cycle-wwk-utilityland | cycle-wwk-utilityland |  | 3 | 0.23 | 3 | 5 |
| cycle-wwk-zendikon | cycle-wwk-zendikon |  | 3 | 0.23 | 3 | 5 |
| cycle-zen-c-kicker | cycle-zen-c-kicker |  | 3 | 0.23 | 3 | 5 |
| cycle-zen-utilityland | cycle-zen-utilityland |  | 3 | 0.23 | 3 | 5 |
| damage-prevention-creature | damage prevention-creature |  | 3 | 0.23 | 3 | 163 |
| deprecated-card-types | deprecated card types |  | 3 | 0.23 | 0 | 257 |
| dilemma | dilemma |  | 3 | 0.23 | 0 | 225 |
| discarded-type-matters | discarded type matters |  | 3 | 0.23 | 2 | 121 |
| disintegrate | disintegrate | burn to exile | 3 | 0.23 | 3 | 67 |
| donate | donate |  | 3 | 0.23 | 3 | 40 |
| donate-token | donate token |  | 3 | 0.23 | 3 | 190 |
| doom-blade | doom blade |  | 3 | 0.23 | 3 | 84 |
| draw-matters | draw matters |  | 3 | 0.23 | 2 | 195 |
| enrage | enrage |  | 3 | 0.23 | 2 | 129 |
| eponymous-planeswalker | eponymous planeswalker |  | 3 | 0.23 | 3 | 43 |
| ferocious | ferocious |  | 3 | 0.23 | 3 | 125 |
| flicker | flicker | blink | 3 | 0.23 | 0 | 216 |
| fog | fog |  | 3 | 0.23 | 1 | 97 |
| free-discard-outlet | free discard outlet |  | 3 | 0.23 | 3 | 69 |
| gives-fear | gives fear |  | 3 | 0.23 | 3 | 29 |
| gives-pp-counters-to-all | gives pp counters to all | gives counters to all | 3 | 0.23 | 3 | 211 |
| gives-tap-ability | gives tap ability |  | 3 | 0.23 | 3 | 218 |
| gives-uncounterable | gives uncounterable |  | 3 | 0.23 | 3 | 32 |
| gives-vigilance | gives vigilance |  | 3 | 0.23 | 3 | 294 |
| hate-full-hand | hate full hand |  | 3 | 0.23 | 3 | 63 |
| hate-color-choose | hate-color-choose |  | 3 | 0.23 | 3 | 96 |
| hate-green | hate-green | green hate | 3 | 0.23 | 3 | 93 |
| hate-instant | hate-instant |  | 3 | 0.23 | 3 | 95 |
| hate-sorcery | hate-sorcery |  | 3 | 0.23 | 3 | 81 |
| hate-tapped | hate-tapped |  | 3 | 0.23 | 3 | 165 |
| hunger-trigger | hunger trigger | hunter trigger | 3 | 0.23 | 1 | 29 |
| lhurgoyf | lhurgoyf |  | 3 | 0.23 | 3 | 116 |
| life-total-matters-self | life-total-matters-self |  | 3 | 0.23 | 3 | 76 |
| lockdown | lockdown |  | 3 | 0.23 | 0 | 130 |
| lockdown-creature | lockdown-creature |  | 3 | 0.23 | 3 | 112 |
| manaless-value | manaless value |  | 3 | 0.23 | 3 | 217 |
| maro-sorcerer | maro-sorcerer |  | 3 | 0.23 | 3 | 88 |
| mathy-name | mathy name |  | 3 | 0.23 | 3 | 29 |
| morbid | morbid |  | 3 | 0.23 | 3 | 132 |
| naturalize-with-set-mechanic | naturalize with set mechanic | naturalize with set's mechanic;disenchant with set mechanic;disenchant with set's mechanic | 3 | 0.23 | 3 | 68 |
| one-sided-fight | one-sided fight | removal-bite;bite | 3 | 0.23 | 3 | 172 |
| onomatopoeia | onomatopoeia |  | 3 | 0.23 | 3 | 15 |
| opponent-chooses | opponent chooses |  | 3 | 0.23 | 2 | 159 |
| overrun | overrun |  | 3 | 0.23 | 3 | 96 |
| play-additional-land | play additional land |  | 3 | 0.23 | 3 | 49 |
| prepare-matters | prepare matters |  | 3 | 0.23 | 3 | 5 |
| protects-planeswalker | protects-planeswalker |  | 3 | 0.23 | 2 | 128 |
| reanimate-from-opponent | reanimate-from-opponent |  | 3 | 0.23 | 1 | 150 |
| recursion-artifact | recursion-artifact |  | 3 | 0.23 | 0 | 163 |
| regenerates-other | regenerates other |  | 3 | 0.23 | 3 | 99 |
| regrowth-land | regrowth-land |  | 3 | 0.23 | 3 | 43 |
| repeatable-impulse | repeatable impulse |  | 3 | 0.23 | 3 | 221 |
| repeatable-plunder | repeatable plunder |  | 3 | 0.23 | 3 | 141 |
| repeatable-rescue | repeatable rescue |  | 3 | 0.23 | 3 | 116 |
| rescue-permanent | rescue-permanent |  | 3 | 0.23 | 3 | 38 |
| restock-all | restock-all |  | 3 | 0.23 | 3 | 46 |
| restricted-blocker | restricted blocker |  | 3 | 0.23 | 1 | 152 |
| rhyming-name | rhyming name |  | 3 | 0.23 | 3 | 159 |
| sacrifice-outlet-planeswalker | sacrifice outlet-planeswalker | sac outlet-planeswalker | 3 | 0.23 | 2 | 70 |
| scales-with-damage-dealt | scales with damage dealt |  | 3 | 0.23 | 2 | 159 |
| selective-group-hug | selective group hug |  | 3 | 0.23 | 3 | 227 |
| shares-name-with-a-mechanic | shares name with a mechanic |  | 3 | 0.23 | 3 | 51 |
| sweeper-graveyard | sweeper-graveyard |  | 3 | 0.23 | 3 | 85 |
| synergy-equipment | synergy-equipment | typal-equipment | 3 | 0.23 | 2 | 255 |
| synergy-low-power | synergy-low-power |  | 3 | 0.23 | 1 | 100 |
| synergy-mountain | synergy-mountain |  | 3 | 0.23 | 3 | 99 |
| synergy-swamp | synergy-swamp |  | 3 | 0.23 | 3 | 102 |
| tap-fuel-power | tap fuel-power |  | 3 | 0.23 | 0 | 350 |
| tapper-land | tapper-land |  | 3 | 0.23 | 3 | 108 |
| temporary-token | temporary token |  | 3 | 0.23 | 3 | 222 |
| tormenting-voice | tormenting voice |  | 3 | 0.23 | 3 | 37 |
| tuck-self | tuck-self |  | 3 | 0.23 | 3 | 63 |
| tutor-instant | tutor-instant |  | 3 | 0.23 | 3 | 26 |
| tutor-land-basic-mountain | tutor-land-basic-mountain |  | 3 | 0.23 | 3 | 18 |
| tutor-land-swamp | tutor-land-swamp | tutor-swamp | 3 | 0.23 | 3 | 31 |
| tutored-by-name | tutored by name |  | 3 | 0.23 | 3 | 151 |
| twiddle | twiddle | tap or untap | 3 | 0.23 | 3 | 70 |
| typal-coupling | typal coupling | tribal coupling | 3 | 0.23 | 3 | 352 |
| typal-dragon | typal-dragon | dragon tribal;tribal-dragon | 3 | 0.23 | 3 | 139 |
| typal-elemental | typal-elemental | tribal-elemental | 3 | 0.23 | 3 | 48 |
| typal-villain | typal-villain | tribal-villain | 3 | 0.23 | 3 | 37 |
| type-errata-hound | type errata hound |  | 3 | 0.23 | 3 | 77 |
| type-errata-obsolete | type errata obsolete |  | 3 | 0.23 | 0 | 43 |
| undergrowth | undergrowth |  | 3 | 0.23 | 2 | 141 |
| unique-p/t | unique p/t |  | 3 | 0.23 | 3 | 39 |
| unpreventable-damage | unpreventable-damage |  | 3 | 0.23 | 3 | 35 |
| upkeep-cost | upkeep cost |  | 3 | 0.23 | 3 | 232 |
| alt-commander | alt-commander |  | 2 | 0.15 | 0 | 165 |
| alternate-win-condition | alternate win condition | automatic win;win condition | 2 | 0.15 | 2 | 87 |
| alternate-cost-bounce | alternate-cost-bounce |  | 2 | 0.15 | 2 | 40 |
| artifactify | artifactify | becomes artifact | 2 | 0.15 | 2 | 79 |
| auto-equip | auto equip | etb-self-attach;snap-on | 2 | 0.15 | 2 | 67 |
| block-additional | block additional |  | 2 | 0.15 | 1 | 42 |
| blood-artist-ability | blood artist ability |  | 2 | 0.15 | 2 | 40 |
| buff-mana | buff mana |  | 2 | 0.15 | 2 | 30 |
| burn-bright-with-set-mechanic | burn bright with set mechanic | trumpet blast w/ set mechanic | 2 | 0.15 | 2 | 21 |
| burn-player-each | burn player-each |  | 2 | 0.15 | 2 | 134 |
| cast-on-resolution | cast on resolution |  | 2 | 0.15 | 2 | 560 |
| catch-up | catch up |  | 2 | 0.15 | 2 | 96 |
| catch-22 | catch-22 |  | 2 | 0.15 | 0 | 88 |
| change-target | change target | redirect target;spell redirection | 2 | 0.15 | 2 | 47 |
| coin-flip | coin flip |  | 2 | 0.15 | 2 | 89 |
| combat-ping | combat ping |  | 2 | 0.15 | 2 | 34 |
| combat-neutral-damage-trigger | combat-neutral damage trigger |  | 2 | 0.15 | 2 | 129 |
| command | command | modal-2/4 | 2 | 0.15 | 0 | 40 |
| conditional-tapland | conditional tapland | etb-self-tapped-conditional | 2 | 0.15 | 0 | 189 |
| cone-spell | cone spell |  | 2 | 0.15 | 2 | 10 |
| counterspell-artifact | counterspell-artifact |  | 2 | 0.15 | 2 | 15 |
| counterspell-instant | counterspell-instant |  | 2 | 0.15 | 2 | 30 |
| cr-107.3f-x-card | cr 107.3f x card | 107.3f x card;rule 107.3f card | 2 | 0.15 | 2 | 33 |
| creature-type-name | creature type name |  | 2 | 0.15 | 2 | 46 |
| creatureland | creatureland | manland;man land | 2 | 0.15 | 2 | 60 |
| cycle-ala-c-tricolor | cycle-ala-c-tricolor |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-c-two-color | cycle-ala-c-two-color |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-charm | cycle-ala-charm |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-forward-ability | cycle-ala-forward-ability |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-naya-soul-spell | cycle-ala-naya-soul-spell |  | 2 | 0.15 | 2 | 3 |
| cycle-ala-obelisk | cycle-ala-obelisk | cycle-obelisk | 2 | 0.15 | 2 | 5 |
| cycle-ala-panorama | cycle-ala-panorama |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-shardland | cycle-ala-shardland |  | 2 | 0.15 | 2 | 5 |
| cycle-ala-u-tricolor | cycle-ala-u-tricolor |  | 2 | 0.15 | 2 | 5 |
| cycle-arb-allied-equipment | cycle-arb-allied-equipment |  | 2 | 0.15 | 2 | 5 |
| cycle-arb-sojourner | cycle-arb-sojourner |  | 2 | 0.15 | 2 | 5 |
| cycle-arb-u-cascade | cycle-arb-u-cascade |  | 2 | 0.15 | 2 | 5 |
| cycle-arb-u-hybrid-gold | cycle-arb-u-hybrid-gold |  | 2 | 0.15 | 2 | 5 |
| cycle-bbd-draft-signpost | cycle-bbd-draft-signpost |  | 2 | 0.15 | 2 | 10 |
| cycle-block-rtr-u-hybrid | cycle-block-rtr-u-hybrid |  | 2 | 0.15 | 2 | 10 |
| cycle-block-zen-monocolor-pw | cycle-block-zen-monocolor-pw |  | 2 | 0.15 | 2 | 5 |
| cycle-csp-enemy-hate | cycle-csp-enemy-hate |  | 2 | 0.15 | 2 | 5 |
| cycle-dmr-draft-signpost | cycle-dmr-draft-signpost |  | 2 | 0.15 | 2 | 10 |
| cycle-ecl-eclipsed | cycle-ecl-eclipsed |  | 2 | 0.15 | 2 | 5 |
| cycle-ecl-student | cycle-ecl-student |  | 2 | 0.15 | 2 | 5 |
| cycle-ecl-typal-kindred | cycle-ecl-typal-kindred |  | 2 | 0.15 | 2 | 5 |
| cycle-elemental-servant | cycle-elemental-servant |  | 2 | 0.15 | 2 | 4 |
| cycle-ema-draft-signpost | cycle-ema-draft-signpost |  | 2 | 0.15 | 2 | 10 |
| cycle-fra-charm | cycle-fra-charm |  | 2 | 0.15 | 2 | 5 |
| cycle-fra-landcycler | cycle-fra-landcycler |  | 2 | 0.15 | 2 | 5 |
| cycle-fra-u-hybrid | cycle-fra-u-hybrid |  | 2 | 0.15 | 2 | 5 |
| cycle-lea-boon | cycle-lea-boon | cycle-boon | 2 | 0.15 | 2 | 5 |
| cycle-m11-titan | cycle-m11-titan |  | 2 | 0.15 | 2 | 5 |
| cycle-m11-u-pw-signature | cycle-m11-u-pw-signature |  | 2 | 0.15 | 2 | 5 |
| cycle-m12-mage | cycle-m12-mage |  | 2 | 0.15 | 2 | 5 |
| cycle-m12-phantasmal | cycle-m12-phantasmal |  | 2 | 0.15 | 2 | 3 |
| cycle-m12-planeswalker | cycle-m12-planeswalker |  | 2 | 0.15 | 2 | 5 |
| cycle-mm2-draft-signpost | cycle-mm2-draft-signpost |  | 2 | 0.15 | 2 | 20 |
| cycle-ody-retriever | cycle-ody-retriever |  | 2 | 0.15 | 2 | 5 |
| cycle-pcy-pitchspell | cycle-pcy-pitchspell |  | 2 | 0.15 | 2 | 5 |
| cycle-sok-maro-spell | cycle-sok-maro-spell |  | 2 | 0.15 | 2 | 5 |
| cycle-som-1mv-combat-trick | cycle-som-1mv-combat-trick | cycle-som-1cmc-combat-trick | 2 | 0.15 | 2 | 5 |
| cycle-som-smith | cycle-som-smith |  | 2 | 0.15 | 2 | 5 |
| cycle-som-spellbomb | cycle-som-spellbomb |  | 2 | 0.15 | 2 | 5 |
| cycle-som-trigon | cycle-som-trigon | cycle-trigon | 2 | 0.15 | 2 | 5 |
| cycle-som-vanilla-creature | cycle-som-vanilla-creature |  | 2 | 0.15 | 2 | 5 |
| cycle-sos-a{a/b}b | cycle-sos-a{a/b}b | cycle-sos-hybrid | 2 | 0.15 | 2 | 5 |
| cycle-sos-draft-signpost | cycle-sos-draft-signpost |  | 2 | 0.15 | 2 | 15 |
| cycle-sos-student | cycle-sos-student |  | 2 | 0.15 | 2 | 5 |
| cycle-spm-draft-signpost | cycle-spm-draft-signpost |  | 2 | 0.15 | 2 | 10 |
| cycle-tr-mage | cycle-tr-mage | trinket mage | 2 | 0.15 | 2 | 7 |
| cycle-triland | cycle-triland |  | 2 | 0.15 | 0 | 35 |
| cycle-triple-tapland | cycle-triple-tapland |  | 2 | 0.15 | 0 | 10 |
| cycle-zen-landfall-self-pump | cycle-zen-landfall-self-pump |  | 2 | 0.15 | 2 | 5 |
| cycle-zen-refugeland | cycle-zen-refugeland |  | 2 | 0.15 | 2 | 5 |
| damage-prevention-you | damage prevention-you |  | 2 | 0.15 | 2 | 160 |
| daunt | daunt |  | 2 | 0.15 | 2 | 42 |
| death-trigger-opponent | death trigger opponent |  | 2 | 0.15 | 2 | 74 |
| deprecated-legend-type | deprecated legend type |  | 2 | 0.15 | 2 | 204 |
| devour | devour |  | 2 | 0.15 | 2 | 26 |
| dnd | dnd |  | 2 | 0.15 | 0 | 472 |
| earthquake | earthquake |  | 2 | 0.15 | 2 | 52 |
| exile-on-resolution | exile on resolution |  | 2 | 0.15 | 2 | 127 |
| exponential | exponential |  | 2 | 0.15 | 2 | 124 |
| fake-flying | fake flying |  | 2 | 0.15 | 2 | 8 |
| faux-targeting | faux targeting | faux target;pseudo target;pseudo targeting | 2 | 0.15 | 2 | 157 |
| flicker-creature | flicker-creature |  | 2 | 0.15 | 1 | 173 |
| flicker-land | flicker-land |  | 2 | 0.15 | 1 | 25 |
| fling | fling |  | 2 | 0.15 | 2 | 33 |
| fog-selective | fog-selective | fog-limited | 2 | 0.15 | 2 | 61 |
| gains-flash | gains flash |  | 2 | 0.15 | 2 | 50 |
| gains-hexproof | gains hexproof |  | 2 | 0.15 | 2 | 73 |
| gains-menace | gains menace |  | 2 | 0.15 | 2 | 134 |
| game-name | game name |  | 2 | 0.15 | 0 | 53 |
| gatefall | gatefall |  | 2 | 0.15 | 2 | 3 |
| gives-defender | gives defender |  | 2 | 0.15 | 2 | 15 |
| gives-double-strike | gives double strike |  | 2 | 0.15 | 2 | 159 |
| gives-infect | gives infect |  | 2 | 0.15 | 2 | 8 |
| gives-reach | gives reach |  | 2 | 0.15 | 2 | 97 |
| grind | grind |  | 2 | 0.15 | 2 | 10 |
| hand-size-increase | hand size increase |  | 2 | 0.15 | 2 | 56 |
| hate-lifegain | hate-lifegain |  | 2 | 0.15 | 2 | 36 |
| hate-low-power | hate-low-power |  | 2 | 0.15 | 0 | 95 |
| hate-nonbasic-land | hate-nonbasic-land |  | 2 | 0.15 | 2 | 82 |
| hate-planeswalker | hate-planeswalker |  | 2 | 0.15 | 2 | 62 |
| hate-typal-human | hate-typal-human | hate-tribal-human | 2 | 0.15 | 2 | 13 |
| hate-wide | hate-wide |  | 2 | 0.15 | 2 | 45 |
| hatebear | hatebear |  | 2 | 0.15 | 2 | 69 |
| hellbending | hellbending |  | 2 | 0.15 | 2 | 95 |
| high-flying | high flying |  | 2 | 0.15 | 2 | 35 |
| hunger | hunger |  | 2 | 0.15 | 2 | 13 |
| impulse-to-zone | impulse-to-zone |  | 2 | 0.15 | 0 | 140 |
| keyword-errata | keyword errata |  | 2 | 0.15 | 0 | 83 |
| land-conversion | land conversion |  | 2 | 0.15 | 2 | 81 |
| leveler | leveler | leveller | 2 | 0.15 | 2 | 26 |
| life-loss-matters | life loss matters |  | 2 | 0.15 | 1 | 163 |
| lifegain-to-damage | lifegain to damage |  | 2 | 0.15 | 2 | 22 |
| lure | lure |  | 2 | 0.15 | 2 | 30 |
| magic-term-name | magic term name |  | 2 | 0.15 | 2 | 24 |
| mana-cost-matters | mana cost matters |  | 2 | 0.15 | 0 | 32 |
| mana-increaser | mana increaser | wild growth;mana doubler;mana flare | 2 | 0.15 | 2 | 64 |
| mana-restriction | mana restriction |  | 2 | 0.15 | 2 | 7 |
| mass-shrink | mass shrink |  | 2 | 0.15 | 2 | 47 |
| mirrored-knight | mirrored knight |  | 2 | 0.15 | 2 | 32 |
| mix-and-match | mix-and-match |  | 2 | 0.15 | 2 | 159 |
| naya-ferocious | naya ferocious |  | 2 | 0.15 | 2 | 27 |
| neo-regenerate | neo-regenerate |  | 2 | 0.15 | 2 | 22 |
| non-mana-ability-mana | non mana ability mana |  | 2 | 0.15 | 2 | 211 |
| off-turn-casting-matters | off-turn casting matters |  | 2 | 0.15 | 2 | 32 |
| old-banish-templating | old banish templating |  | 2 | 0.15 | 2 | 16 |
| opponent-lifegain | opponent lifegain |  | 2 | 0.15 | 2 | 59 |
| pair-commander | pair-commander |  | 2 | 0.15 | 2 | 247 |
| phase-manipulation | phase manipulation |  | 2 | 0.15 | 1 | 108 |
| pillowfort | pillowfort |  | 2 | 0.15 | 1 | 64 |
| pitch-spell | pitch spell | alternate-cost-pitch | 2 | 0.15 | 0 | 43 |
| power-doubler | power doubler |  | 2 | 0.15 | 2 | 66 |
| protects-permanent | protects-permanent |  | 2 | 0.15 | 2 | 46 |
| provoke-lite | provoke lite |  | 2 | 0.15 | 2 | 26 |
| punisher | punisher | villainous choice | 2 | 0.15 | 0 | 174 |
| random-discard | random discard |  | 2 | 0.15 | 2 | 39 |
| reanimate-artifact | reanimate-artifact |  | 2 | 0.15 | 2 | 77 |
| reanimate-from-any | reanimate-from-any |  | 2 | 0.15 | 2 | 99 |
| recursion-instant | recursion-instant |  | 2 | 0.15 | 0 | 102 |
| recursion-permanent | recursion-permanent |  | 2 | 0.15 | 0 | 122 |
| recursion-sorcery | recursion-sorcery |  | 2 | 0.15 | 0 | 101 |
| regrowth-instant | regrowth-instant |  | 2 | 0.15 | 2 | 79 |
| regrowth-permanent | regrowth-permanent |  | 2 | 0.15 | 2 | 62 |
| regrowth-sorcery | regrowth-sorcery |  | 2 | 0.15 | 2 | 80 |
| removal-noncreature | removal-noncreature |  | 2 | 0.15 | 2 | 15 |
| repeatable-impulsive-draw | repeatable impulsive draw |  | 2 | 0.15 | 2 | 179 |
| repeatable-modal-choice | repeatable modal choice |  | 2 | 0.15 | 2 | 133 |
| repeatable-rummage | repeatable rummage |  | 2 | 0.15 | 2 | 140 |
| repeatable-scry | repeatable scry |  | 2 | 0.15 | 2 | 186 |
| repeatable-treasures | repeatable treasures |  | 2 | 0.15 | 2 | 218 |
| restricted-mana | restricted mana |  | 2 | 0.15 | 2 | 247 |
| ritual | ritual |  | 2 | 0.15 | 2 | 71 |
| school-name | school name |  | 2 | 0.15 | 2 | 19 |
| shardland | shardland | cycle-shardland | 2 | 0.15 | 0 | 30 |
| sneak-land | sneak-land |  | 2 | 0.15 | 2 | 80 |
| state-trigger | state trigger |  | 2 | 0.15 | 2 | 66 |
| synergy-arcane | synergy-arcane |  | 2 | 0.15 | 2 | 81 |
| synergy-aura | synergy-aura |  | 2 | 0.15 | 2 | 200 |
| synergy-basic | synergy-basic |  | 2 | 0.15 | 2 | 66 |
| synergy-blocker | synergy-blocker |  | 2 | 0.15 | 2 | 105 |
| synergy-color-choose | synergy-color-choose |  | 2 | 0.15 | 2 | 22 |
| synergy-flying | synergy-flying |  | 2 | 0.15 | 2 | 116 |
| synergy-graveyard-cast | synergy-graveyard-cast |  | 2 | 0.15 | 1 | 92 |
| synergy-scry | synergy-scry | scry matters | 2 | 0.15 | 2 | 30 |
| synergy-surveil | synergy-surveil |  | 2 | 0.15 | 2 | 21 |
| theft-artifact | theft-artifact |  | 2 | 0.15 | 2 | 58 |
| threaten-with-set's-mechanic | threaten with set's mechanic |  | 2 | 0.15 | 2 | 52 |
| times-resolved-matters | times resolved matters | variable effect, same ability;same ability, variable effect | 2 | 0.15 | 2 | 33 |
| triland | triland |  | 2 | 0.15 | 0 | 44 |
| tunneling | tunneling |  | 2 | 0.15 | 2 | 30 |
| tutor-creature | tutor-creature |  | 2 | 0.15 | 2 | 219 |
| tutor-land-any | tutor-land-any |  | 2 | 0.15 | 2 | 45 |
| tutor-land-basic-swamp | tutor-land-basic-swamp |  | 2 | 0.15 | 2 | 16 |
| tutor-land-forest | tutor-land-forest | tutor-forest | 2 | 0.15 | 2 | 49 |
| tutor-land-gate | tutor-land-gate | tutor-gate | 2 | 0.15 | 2 | 7 |
| tutor-land-island | tutor-land-island | tutor-island | 2 | 0.15 | 2 | 28 |
| tutor-land-mountain | tutor-land-mountain | tutor-mountain | 2 | 0.15 | 2 | 34 |
| tutor-land-plains | tutor-land-plains | tutor-plains | 2 | 0.15 | 2 | 46 |
| tutor-sorcery | tutor-sorcery |  | 2 | 0.15 | 2 | 19 |
| tutor-to-graveyard | tutor-to-graveyard | entomb;tutor-entomb | 2 | 0.15 | 2 | 35 |
| tutors-by-name | tutors by name |  | 2 | 0.15 | 2 | 145 |
| typal-choose | typal-choose | tribal-choose | 2 | 0.15 | 2 | 95 |
| typal-faerie | typal-faerie | tribal-faerie | 2 | 0.15 | 2 | 35 |
| typal-human | typal-human | human tribal;tribal-human | 2 | 0.15 | 2 | 105 |
| typal-merfolk | typal-merfolk | tribal-merfolk | 2 | 0.15 | 2 | 85 |
| typal-soldier | typal-soldier | tribal-soldier | 2 | 0.15 | 2 | 54 |
| typal-spirit | typal-spirit | tribal-spirit;synergy-spirit;spirit lord | 2 | 0.15 | 2 | 129 |
| type-addition-noble | type addition noble |  | 2 | 0.15 | 2 | 24 |
| type-errata-lord | type errata lord |  | 2 | 0.15 | 2 | 25 |
| type-errata-specific-cat | type errata specific cat |  | 2 | 0.15 | 0 | 12 |
| type-errata-viashino | type errata viashino |  | 2 | 0.15 | 2 | 58 |
| unique-type-exclusion | unique-type-exclusion |  | 2 | 0.15 | 2 | 40 |
| unprinted-token | unprinted token |  | 2 | 0.15 | 2 | 141 |
| unstoppable | unstoppable | super-trample | 2 | 0.15 | 2 | 15 |
| untapper-artifact | untapper-artifact |  | 2 | 0.15 | 1 | 140 |
| untaps-self | untaps self | untapper-self | 2 | 0.15 | 2 | 182 |
| vanilla-aura | vanilla aura |  | 2 | 0.15 | 2 | 45 |
| weaker-in-singleton-formats | weaker in singleton formats | worse in singleton | 2 | 0.15 | 1 | 115 |
| werewolf-mechanic | werewolf mechanic |  | 2 | 0.15 | 2 | 69 |
| wheel | wheel |  | 2 | 0.15 | 0 | 165 |
| wind-drake-with-set's-mechanic | wind drake with set's mechanic | wind drake with set mechanic | 2 | 0.15 | 2 | 34 |
| wingman | wingman |  | 2 | 0.15 | 2 | 38 |
| x-cost-matters | x cost matters |  | 2 | 0.15 | 2 | 23 |
| young-pyromancer-ability | young pyromancer ability |  | 2 | 0.15 | 2 | 43 |
| ablative-armor | ablative armor |  | 1 | 0.08 | 1 | 23 |
| abrade | abrade |  | 1 | 0.08 | 1 | 43 |
| abyss | abyss |  | 1 | 0.08 | 1 | 40 |
| affinity-for-artifacts | affinity for artifacts |  | 1 | 0.08 | 1 | 42 |
| affinity-for-graveyard | affinity for graveyard |  | 1 | 0.08 | 0 | 28 |
| affinity-for-land-type | affinity for land type |  | 1 | 0.08 | 1 | 16 |
| affinity-for-spells | affinity for spells | affinity for spells in graveyard | 1 | 0.08 | 1 | 11 |
| afflict | afflict |  | 1 | 0.08 | 1 | 18 |
| alternate-loss-condition | alternate loss condition |  | 1 | 0.08 | 1 | 39 |
| alternate-equip-cost | alternate-equip-cost |  | 1 | 0.08 | 1 | 36 |
| anagram | anagram |  | 1 | 0.08 | 1 | 45 |
| arc-lightning | arc lightning |  | 1 | 0.08 | 1 | 18 |
| armament-ability | armament ability |  | 1 | 0.08 | 1 | 17 |
| armoring | armoring | shielding;buttbreathing | 1 | 0.08 | 1 | 43 |
| artifactfall | artifactfall |  | 1 | 0.08 | 1 | 99 |
| auto-buyback | auto buyback |  | 1 | 0.08 | 1 | 24 |
| berserk | berserk |  | 1 | 0.08 | 1 | 19 |
| block-unlimited | block unlimited |  | 1 | 0.08 | 1 | 12 |
| bounceland | bounceland | karoo land | 1 | 0.08 | 0 | 17 |
| burn-self | burn-self | stop hitting yourself | 1 | 0.08 | 1 | 14 |
| buttstrike | buttstrike | doran effect;backbone | 1 | 0.08 | 1 | 24 |
| catalog | catalog |  | 1 | 0.08 | 1 | 51 |
| cda-toughness | cda-toughness |  | 1 | 0.08 | 1 | 194 |
| change-name | change name |  | 1 | 0.08 | 1 | 13 |
| chromatic-lantern | chromatic lantern |  | 1 | 0.08 | 1 | 68 |
| circle-of-protection | circle of protection |  | 1 | 0.08 | 0 | 21 |
| clone | clone |  | 1 | 0.08 | 1 | 77 |
| commander-identity-matters | commander identity matters |  | 1 | 0.08 | 1 | 10 |
| commander-matters | commander matters |  | 1 | 0.08 | 0 | 54 |
| compulsive-research | compulsive research | thirst for | 1 | 0.08 | 1 | 13 |
| copy-ability | copy-ability |  | 1 | 0.08 | 1 | 50 |
| copy-noncreature | copy-noncreature |  | 1 | 0.08 | 1 | 4 |
| copy-self | copy-self |  | 1 | 0.08 | 1 | 330 |
| copy-token | copy-token |  | 1 | 0.08 | 1 | 57 |
| cost-reducer-instant | cost-reducer-instant |  | 1 | 0.08 | 0 | 43 |
| cost-reducer-instant-sorcery | cost-reducer-instant-sorcery |  | 1 | 0.08 | 1 | 41 |
| cost-reducer-sorcery | cost-reducer-sorcery |  | 1 | 0.08 | 0 | 42 |
| counter-doubler | counter doubler |  | 1 | 0.08 | 1 | 66 |
| counter-fuel-mm | counter fuel-mm |  | 1 | 0.08 | 1 | 11 |
| counter-fuel-pp | counter fuel-pp |  | 1 | 0.08 | 1 | 103 |
| counter-increaser | counter increaser |  | 1 | 0.08 | 0 | 88 |
| counterspell-free | counterspell-free |  | 1 | 0.08 | 1 | 13 |
| counterspell-sacrifice | counterspell-sacrifice |  | 1 | 0.08 | 1 | 31 |
| counterspell-sorcery | counterspell-sorcery |  | 1 | 0.08 | 1 | 28 |
| creature-type-monster | creature type monster |  | 1 | 0.08 | 1 | 3 |
| cycle-2xm-r-two-color | cycle-2xm-r-two-color |  | 1 | 0.08 | 1 | 20 |
| cycle-5dn-beacon | cycle-5dn-beacon |  | 1 | 0.08 | 1 | 5 |
| cycle-a25-draft-signpost | cycle-a25-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-akh-draft-signpost | cycle-akh-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-ala-allied-2-drop | cycle-ala-allied-2-drop |  | 1 | 0.08 | 1 | 5 |
| cycle-ala-backward-ability | cycle-ala-backward-ability |  | 1 | 0.08 | 1 | 5 |
| cycle-ala-herald | cycle-ala-herald |  | 1 | 0.08 | 1 | 5 |
| cycle-ala-naya-cycler | cycle-ala-naya-cycler |  | 1 | 0.08 | 1 | 3 |
| cycle-ala-resounding-spell | cycle-ala-resounding-spell | cycle-resounding-spell | 1 | 0.08 | 1 | 5 |
| cycle-apc-c-two-color | cycle-apc-c-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-apc-phyrexian-vertical | cycle-apc-phyrexian-vertical |  | 1 | 0.08 | 1 | 3 |
| cycle-arb-borderposts | cycle-arb-borderposts |  | 1 | 0.08 | 1 | 5 |
| cycle-arb-c-enemy | cycle-arb-c-enemy |  | 1 | 0.08 | 1 | 5 |
| cycle-arb-c-hybrid-gold | cycle-arb-c-hybrid-gold |  | 1 | 0.08 | 1 | 5 |
| cycle-arb-crossed-shard | cycle-arb-crossed-shard |  | 1 | 0.08 | 1 | 5 |
| cycle-avr-u-miracle | cycle-avr-u-miracle |  | 1 | 0.08 | 1 | 4 |
| cycle-block-rav-colors-matter | cycle-block-rav-colors-matter |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rav-guild-champion | cycle-block-rav-guild-champion |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rav-guildmage | cycle-block-rav-guildmage |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rav-mnn | cycle-block-rav-mnn |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rav-r-hybrid | cycle-block-rav-r-hybrid |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rtr-guildmaster | cycle-block-rtr-guildmaster |  | 1 | 0.08 | 1 | 10 |
| cycle-block-rtr-off-color | cycle-block-rtr-off-color |  | 1 | 0.08 | 1 | 10 |
| cycle-bok-flip-creature | cycle-bok-flip-creature |  | 1 | 0.08 | 1 | 5 |
| cycle-c15-reprint-commander | cycle-c15-reprint-commander |  | 1 | 0.08 | 1 | 5 |
| cycle-c17-alt-commander | cycle-c17-alt-commander |  | 1 | 0.08 | 1 | 8 |
| cycle-chk-myojin | cycle-chk-myojin |  | 1 | 0.08 | 1 | 5 |
| cycle-clb-alt-commander | cycle-clb-alt-commander |  | 1 | 0.08 | 1 | 4 |
| cycle-cmm-draft-signpost | cycle-cmm-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-cmr-forward-partner | cycle-cmr-forward-partner |  | 1 | 0.08 | 1 | 10 |
| cycle-cns-draft-signpost | cycle-cns-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-con-basic-landcycling | cycle-con-basic-landcycling |  | 1 | 0.08 | 1 | 5 |
| cycle-con-enemy-hate | cycle-con-enemy-hate |  | 1 | 0.08 | 1 | 5 |
| cycle-con-esper-artifact-boost | cycle-con-esper-artifact-boost |  | 1 | 0.08 | 1 | 3 |
| cycle-con-outlander | cycle-con-outlander |  | 1 | 0.08 | 1 | 5 |
| cycle-con-u-tricolor | cycle-con-u-tricolor |  | 1 | 0.08 | 1 | 5 |
| cycle-con-u-two-color | cycle-con-u-two-color |  | 1 | 0.08 | 1 | 5 |
| cycle-cycling-land | cycle-cycling-land |  | 1 | 0.08 | 0 | 36 |
| cycle-dis-u-split | cycle-dis-u-split |  | 1 | 0.08 | 1 | 5 |
| cycle-dka-allied-flashback | cycle-dka-allied-flashback |  | 1 | 0.08 | 1 | 5 |
| cycle-dka-draft-signpost | cycle-dka-draft-signpost |  | 1 | 0.08 | 0 | 9 |
| cycle-dka-enemy-flashback | cycle-dka-enemy-flashback |  | 1 | 0.08 | 1 | 5 |
| cycle-dka-enemy-utilityland | cycle-dka-enemy-utilityland |  | 1 | 0.08 | 1 | 5 |
| cycle-dka-m-monster | cycle-dka-m-monster |  | 1 | 0.08 | 1 | 4 |
| cycle-dmu-cost-reduction | cycle-dmu-cost-reduction |  | 1 | 0.08 | 1 | 5 |
| cycle-dmu-draft-signpost | cycle-dmu-draft-signpost |  | 1 | 0.08 | 0 | 20 |
| cycle-dmu-mmn-signpost | cycle-dmu-mmn-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-dom-draft-signpost | cycle-dom-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-dom-m-legend | cycle-dom-m-legend |  | 1 | 0.08 | 1 | 5 |
| cycle-dom-r-mmm-creature | cycle-dom-r-mmm-creature |  | 1 | 0.08 | 1 | 5 |
| cycle-dtk-draft-signpost | cycle-dtk-draft-signpost | cycle-dtk-u-two-color-dragon | 1 | 0.08 | 1 | 5 |
| cycle-dtk-khan | cycle-dtk-khan |  | 1 | 0.08 | 1 | 5 |
| cycle-ecl-champion | cycle-ecl-champion |  | 1 | 0.08 | 1 | 5 |
| cycle-ecl-command | cycle-ecl-command |  | 1 | 0.08 | 1 | 5 |
| cycle-ecl-r-dfc | cycle-ecl-r-dfc |  | 1 | 0.08 | 1 | 5 |
| cycle-eld-court-leader | cycle-eld-court-leader |  | 1 | 0.08 | 1 | 5 |
| cycle-eld-syr-legend | cycle-eld-syr-legend |  | 1 | 0.08 | 1 | 5 |
| cycle-exo-retriever | cycle-exo-retriever |  | 1 | 0.08 | 1 | 5 |
| cycle-fdn-r-two-color | cycle-fdn-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-fra-ally-hoser | cycle-fra-ally-hoser |  | 1 | 0.08 | 1 | 5 |
| cycle-fra-commons | cycle-fra-commons |  | 1 | 0.08 | 1 | 5 |
| cycle-fra-r-two-color | cycle-fra-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-fra-walkerland | cycle-fra-walkerland |  | 1 | 0.08 | 0 | 10 |
| cycle-fut-scry-reveal | cycle-fut-scry-reveal |  | 1 | 0.08 | 1 | 5 |
| cycle-gtc-m-two-color | cycle-gtc-m-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-hybrid-modal | cycle-hybrid-modal |  | 1 | 0.08 | 0 | 10 |
| cycle-ice-r-tricolor | cycle-ice-r-tricolor |  | 1 | 0.08 | 1 | 5 |
| cycle-ima-r-two-color | cycle-ima-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-inr-r-two-color | cycle-inr-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-inv-c-ally-kicker-spell | cycle-inv-c-ally-kicker-spell |  | 1 | 0.08 | 1 | 5 |
| cycle-inv-c-two-color | cycle-inv-c-two-color |  | 1 | 0.08 | 1 | 5 |
| cycle-inv-dual-tapland | cycle-inv-dual-tapland |  | 1 | 0.08 | 1 | 5 |
| cycle-inv-split-card | cycle-inv-split-card |  | 1 | 0.08 | 1 | 5 |
| cycle-isd-draft-signpost | cycle-isd-draft-signpost | cycle-isd-enemy-flashback | 1 | 0.08 | 1 | 5 |
| cycle-jou-dictate | cycle-jou-dictate |  | 1 | 0.08 | 1 | 5 |
| cycle-kld-draft-signpost | cycle-kld-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-lea-circle-protection | cycle-lea-circle-protection |  | 1 | 0.08 | 1 | 5 |
| cycle-lrw-command | cycle-lrw-command |  | 1 | 0.08 | 1 | 5 |
| cycle-lrw-lorwyn-five | cycle-lrw-lorwyn-five | lorwyn five | 1 | 0.08 | 1 | 5 |
| cycle-lrw-typal-land | cycle-lrw-typal-land | cycle-lrw-tribal-land | 1 | 0.08 | 1 | 8 |
| cycle-lrw-typal-lord | cycle-lrw-typal-lord |  | 1 | 0.08 | 1 | 8 |
| cycle-m10-typal-lord | cycle-m10-typal-lord |  | 1 | 0.08 | 1 | 5 |
| cycle-m12-artifact-of-empires | cycle-m12-artifact-of-empires |  | 1 | 0.08 | 1 | 3 |
| cycle-m12-r-pw-signature | cycle-m12-r-pw-signature |  | 1 | 0.08 | 1 | 5 |
| cycle-m14-pw-signature | cycle-m14-pw-signature |  | 1 | 0.08 | 1 | 5 |
| cycle-m14-r-enemy-hate | cycle-m14-r-enemy-hate |  | 1 | 0.08 | 1 | 5 |
| cycle-m15-wall | cycle-m15-wall |  | 1 | 0.08 | 1 | 5 |
| cycle-m19-draft-signpost | cycle-m19-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-m19-mare | cycle-m19-mare |  | 1 | 0.08 | 1 | 6 |
| cycle-m19-monocolor-legend | cycle-m19-monocolor-legend |  | 1 | 0.08 | 1 | 5 |
| cycle-m19-precon-r | cycle-m19-precon-r |  | 1 | 0.08 | 1 | 5 |
| cycle-m20-draft-signpost | cycle-m20-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-m20-enemy-hate | cycle-m20-enemy-hate |  | 1 | 0.08 | 1 | 5 |
| cycle-m20-precon-u | cycle-m20-precon-u |  | 1 | 0.08 | 1 | 5 |
| cycle-m21-garruk-vertical | cycle-m21-garruk-vertical |  | 1 | 0.08 | 1 | 4 |
| cycle-mbs-sun-zenith | cycle-mbs-sun-zenith |  | 1 | 0.08 | 1 | 5 |
| cycle-mm2-r-two-color | cycle-mm2-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-mm3-r-tricolor | cycle-mm3-r-tricolor |  | 1 | 0.08 | 1 | 5 |
| cycle-mm3-u-tricolor | cycle-mm3-u-tricolor |  | 1 | 0.08 | 1 | 5 |
| cycle-mmq-ability-wall | cycle-mmq-ability-wall |  | 1 | 0.08 | 1 | 5 |
| cycle-mmq-alpha-spellshaper | cycle-mmq-alpha-spellshaper |  | 1 | 0.08 | 1 | 5 |
| cycle-monocolor-atog | cycle-monocolor-atog |  | 1 | 0.08 | 1 | 5 |
| cycle-mor-banneret | cycle-mor-banneret |  | 1 | 0.08 | 1 | 5 |
| cycle-mrd-c-entwine | cycle-mrd-c-entwine |  | 1 | 0.08 | 1 | 5 |
| cycle-mrd-spellbomb | cycle-mrd-spellbomb |  | 1 | 0.08 | 1 | 5 |
| cycle-nightscape-vertical | cycle-nightscape-vertical |  | 1 | 0.08 | 1 | 4 |
| cycle-one-r-two-color | cycle-one-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-ons-lord | cycle-ons-lord |  | 1 | 0.08 | 1 | 6 |
| cycle-ons-m-cycling-land | cycle-ons-m-cycling-land | cycle-m-cycling-land;cycle-ons-cycling-land | 1 | 0.08 | 1 | 5 |
| cycle-ons-pit-fighter | cycle-ons-pit-fighter |  | 1 | 0.08 | 1 | 5 |
| cycle-ori-pivotal-moment | cycle-ori-pivotal-moment |  | 1 | 0.08 | 1 | 5 |
| cycle-pcy-avatar | cycle-pcy-avatar |  | 1 | 0.08 | 1 | 5 |
| cycle-plc-alternate-reality-legend | cycle-plc-alternate-reality-legend | cycle-alternate-reality-legend | 1 | 0.08 | 1 | 5 |
| cycle-plc-rescue-vertical | cycle-plc-rescue-vertical |  | 1 | 0.08 | 1 | 4 |
| cycle-plc-tsb-colorshift | cycle-plc-tsb-colorshift |  | 1 | 0.08 | 1 | 5 |
| cycle-pls-familiar | cycle-pls-familiar |  | 1 | 0.08 | 1 | 5 |
| cycle-pls-u-gating-creature | cycle-pls-u-gating-creature |  | 1 | 0.08 | 1 | 5 |
| cycle-rav-backward-boost | cycle-rav-backward-boost |  | 1 | 0.08 | 1 | 10 |
| cycle-rav-bounceland | cycle-rav-bounceland |  | 1 | 0.08 | 1 | 10 |
| cycle-rav-forward-boost | cycle-rav-forward-boost |  | 1 | 0.08 | 1 | 10 |
| cycle-rav-signet | cycle-rav-signet |  | 1 | 0.08 | 1 | 10 |
| cycle-rix-elder-dinosaur | cycle-rix-elder-dinosaur |  | 1 | 0.08 | 1 | 6 |
| cycle-roe-r-leveler | cycle-roe-r-leveler |  | 1 | 0.08 | 1 | 5 |
| cycle-rvr-c-hybrid | cycle-rvr-c-hybrid |  | 1 | 0.08 | 1 | 10 |
| cycle-rvr-c-two-color | cycle-rvr-c-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-rvr-r-two-color-legend | cycle-rvr-r-two-color-legend |  | 1 | 0.08 | 1 | 10 |
| cycle-rvr-u-two-color | cycle-rvr-u-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-scg-5m-landcycler | cycle-scg-5m-landcycler |  | 1 | 0.08 | 1 | 5 |
| cycle-shm-basic-land-count | cycle-shm-basic-land-count |  | 1 | 0.08 | 1 | 5 |
| cycle-shm-hybrid-modal | cycle-shm-hybrid-modal |  | 1 | 0.08 | 1 | 5 |
| cycle-shm-liege | cycle-shm-liege |  | 1 | 0.08 | 1 | 10 |
| cycle-shm-utilityland | cycle-shm-utilityland |  | 1 | 0.08 | 1 | 5 |
| cycle-sok-shinen | cycle-sok-shinen |  | 1 | 0.08 | 1 | 5 |
| cycle-som-c-metalcraft | cycle-som-c-metalcraft |  | 1 | 0.08 | 1 | 5 |
| cycle-som-color-artifact | cycle-som-color-artifact |  | 1 | 0.08 | 1 | 5 |
| cycle-sos-mascot | cycle-sos-mascot |  | 1 | 0.08 | 1 | 5 |
| cycle-sos-mono-u-legend | cycle-sos-mono-u-legend |  | 1 | 0.08 | 1 | 5 |
| cycle-sos-surveil-dual | cycle-sos-surveil-dual | cycle-sos-surveil-land | 1 | 0.08 | 1 | 5 |
| cycle-spm-c-hybrid | cycle-spm-c-hybrid |  | 1 | 0.08 | 1 | 5 |
| cycle-spm-r-hybrid | cycle-spm-r-hybrid |  | 1 | 0.08 | 1 | 5 |
| cycle-spm-r-two-color | cycle-spm-r-two-color |  | 1 | 0.08 | 1 | 10 |
| cycle-spm-surveil-dual | cycle-spm-surveil-dual | cycle-spm-surveil-land | 1 | 0.08 | 1 | 5 |
| cycle-stx-c-hybrid-spell | cycle-stx-c-hybrid-spell |  | 1 | 0.08 | 1 | 5 |
| cycle-ths-ordeal | cycle-ths-ordeal |  | 1 | 0.08 | 1 | 5 |
| cycle-tor-c-flashback | cycle-tor-c-flashback |  | 1 | 0.08 | 1 | 5 |
| cycle-tsp-forward-flashback | cycle-tsp-forward-flashback |  | 1 | 0.08 | 1 | 5 |
| cycle-tsp-spellshaper | cycle-tsp-spellshaper |  | 1 | 0.08 | 1 | 5 |
| cycle-tsp-two-color-legend | cycle-tsp-two-color-legend |  | 1 | 0.08 | 1 | 5 |
| cycle-tsp-u-split-second | cycle-tsp-u-split-second |  | 1 | 0.08 | 1 | 5 |
| cycle-vma-draft-signpost | cycle-vma-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-vow-r-two-color-legend | cycle-vow-r-two-color-legend |  | 1 | 0.08 | 1 | 10 |
| cycle-w16-r | cycle-w16-r |  | 1 | 0.08 | 1 | 5 |
| cycle-w17-r-creature | cycle-w17-r-creature |  | 1 | 0.08 | 1 | 5 |
| cycle-war-finale | cycle-war-finale |  | 1 | 0.08 | 1 | 5 |
| cycle-woe-draft-signpost | cycle-woe-draft-signpost |  | 1 | 0.08 | 1 | 10 |
| cycle-wwk-quest | cycle-wwk-quest |  | 1 | 0.08 | 1 | 4 |
| cycle-zen-c-growing-ally | cycle-zen-c-growing-ally |  | 1 | 0.08 | 1 | 5 |
| cycle-zen-expedition | cycle-zen-expedition |  | 1 | 0.08 | 1 | 5 |
| cycle-zen-strong-kicker | cycle-zen-strong-kicker |  | 1 | 0.08 | 1 | 5 |
| damage-multiplier | damage multiplier | damage doubler;damage tripler | 1 | 0.08 | 1 | 55 |
| damage-prevention-planeswalker | damage prevention-planeswalker |  | 1 | 0.08 | 1 | 26 |
| damage-prevention-player | damage prevention-player |  | 1 | 0.08 | 1 | 25 |
| day-zero-errata | day zero errata | day 0 errata;day zero oracle errata;day 0 oracle errata | 1 | 0.08 | 1 | 44 |
| deal-with-the-devil | deal with the devil |  | 1 | 0.08 | 1 | 49 |
| deanimate | deanimate |  | 1 | 0.08 | 1 | 24 |
| defector | defector | board-walking | 1 | 0.08 | 1 | 67 |
| deprecated-mechanics | deprecated mechanics |  | 1 | 0.08 | 0 | 369 |
| detain | detain |  | 1 | 0.08 | 1 | 18 |
| discard-to-exile | discard to exile | discard-exile | 1 | 0.08 | 1 | 92 |
| division | division |  | 1 | 0.08 | 1 | 95 |
| divvy | divvy |  | 1 | 0.08 | 0 | 35 |
| dnd-character | dnd character |  | 1 | 0.08 | 1 | 206 |
| dnd-spell | dnd spell | d&d spell | 1 | 0.08 | 1 | 42 |
| doctor-who-episode-name | doctor who episode name | dr who episode name | 1 | 0.08 | 1 | 39 |
| draw-hate | draw hate | hate-draw | 1 | 0.08 | 1 | 62 |
| drawlink | drawlink |  | 1 | 0.08 | 0 | 20 |
| emblem-lite | emblem-lite |  | 1 | 0.08 | 1 | 16 |
| exchange-control | exchange control | theft-exchange | 1 | 0.08 | 1 | 46 |
| exile-with-counter | exile with counter |  | 1 | 0.08 | 1 | 20 |
| explore-like | explore-like |  | 1 | 0.08 | 1 | 15 |
| extra-combat-phase | extra combat phase | extra attack;extra combat | 1 | 0.08 | 1 | 54 |
| extract | extract |  | 1 | 0.08 | 1 | 45 |
| face-commander | face-commander |  | 1 | 0.08 | 1 | 168 |
| fact-or-fiction | fact or fiction |  | 1 | 0.08 | 1 | 22 |
| finality-counter | finality counter |  | 1 | 0.08 | 1 | 46 |
| firebend-like | firebend-like |  | 1 | 0.08 | 1 | 46 |
| flicker-artifact | flicker-artifact |  | 1 | 0.08 | 0 | 49 |
| flicker-enchantment | flicker-enchantment |  | 1 | 0.08 | 0 | 35 |
| flicker-permanent | flicker-permanent |  | 1 | 0.08 | 1 | 18 |
| flicker-planeswalker | flicker-planeswalker |  | 1 | 0.08 | 0 | 34 |
| flicker-slow | flicker-slow | blink-slow | 1 | 0.08 | 1 | 116 |
| fling-self | fling-self |  | 1 | 0.08 | 1 | 12 |
| force-shuffle | force shuffle | forced opponent shuffle | 1 | 0.08 | 1 | 192 |
| formidable | formidable |  | 1 | 0.08 | 1 | 25 |
| freeze-permanent-any | freeze-permanent-any | freeze-permanent;freeze-any;stun-permanent-any;stun-permanent;stun-any | 1 | 0.08 | 1 | 6 |
| full-refund | full refund |  | 1 | 0.08 | 1 | 105 |
| functional-reminder-counter | functional reminder counter |  | 1 | 0.08 | 1 | 19 |
| gains-infect | gains infect |  | 1 | 0.08 | 1 | 4 |
| gains-intimidate | gains intimidate |  | 1 | 0.08 | 1 | 9 |
| gains-lifelink | gains lifelink |  | 1 | 0.08 | 1 | 153 |
| gating | gating |  | 1 | 0.08 | 0 | 13 |
| gives-castable-from-graveyard | gives castable from graveyard | cast from graveyard | 1 | 0.08 | 0 | 160 |
| gives-castable-from-library | gives castable from library | cast from library | 1 | 0.08 | 0 | 98 |
| gives-changeling | gives changeling | grants changeling | 1 | 0.08 | 1 | 19 |
| gives-conspire | gives conspire |  | 1 | 0.08 | 1 | 3 |
| gives-drawlink | gives drawlink |  | 1 | 0.08 | 1 | 8 |
| gives-fake-flying | gives fake flying |  | 1 | 0.08 | 1 | 3 |
| gives-mana-ability | gives mana ability |  | 1 | 0.08 | 1 | 105 |
| gives-menace | gives menace |  | 1 | 0.08 | 1 | 186 |
| gives-persist | gives persist |  | 1 | 0.08 | 1 | 7 |
| gives-poisonous | gives poisonous |  | 1 | 0.08 | 1 | 6 |
| gives-undaunted | gives undaunted |  | 1 | 0.08 | 1 | 2 |
| gives-ward | gives ward |  | 1 | 0.08 | 1 | 71 |
| gives-wither | gives wither |  | 1 | 0.08 | 1 | 11 |
| grave-pact | grave pact |  | 1 | 0.08 | 1 | 7 |
| graveyard-seal | graveyard seal |  | 1 | 0.08 | 1 | 58 |
| guess | guess |  | 1 | 0.08 | 1 | 43 |
| hate-empty-hand | hate empty hand |  | 1 | 0.08 | 0 | 37 |
| hate-activation | hate-activation |  | 1 | 0.08 | 1 | 36 |
| hate-aura | hate-aura |  | 1 | 0.08 | 1 | 26 |
| hate-creatureland | hate-creatureland |  | 1 | 0.08 | 1 | 4 |
| hate-defender | hate-defender |  | 1 | 0.08 | 1 | 7 |
| hate-equipment | hate-equipment |  | 1 | 0.08 | 1 | 22 |
| hate-infect | hate-infect |  | 1 | 0.08 | 1 | 3 |
| hate-legendary | hate-legendary |  | 1 | 0.08 | 1 | 21 |
| hate-named | hate-named |  | 1 | 0.08 | 1 | 71 |
| hate-theft | hate-theft | punish theft | 1 | 0.08 | 0 | 98 |
| hate-typal-goat | hate-typal-goat | hate-tribal-goat | 1 | 0.08 | 1 | 3 |
| hate-typal-goblin | hate-typal-goblin | hate-tribal-goblin | 1 | 0.08 | 1 | 15 |
| hate-typal-vampire | hate-typal-vampire | hate-tribal-vampire | 1 | 0.08 | 1 | 11 |
| hate-typal-wall | hate-typal-wall | hate-tribal-wall | 1 | 0.08 | 1 | 27 |
| hate-typal-zombie | hate-typal-zombie | hate-tribal-zombie | 1 | 0.08 | 1 | 17 |
| haven | haven |  | 1 | 0.08 | 1 | 75 |
| heroic | heroic |  | 1 | 0.08 | 1 | 135 |
| high-x-matters | high x matters |  | 1 | 0.08 | 1 | 40 |
| homeward-effect | homeward effect | regain control | 1 | 0.08 | 1 | 86 |
| howlgeist-ability | howlgeist ability |  | 1 | 0.08 | 1 | 12 |
| hurricane | hurricane |  | 1 | 0.08 | 1 | 35 |
| impact-effect | impact effect |  | 1 | 0.08 | 1 | 60 |
| imprint | imprint | encoded | 1 | 0.08 | 1 | 109 |
| impulse-artifact | impulse-artifact |  | 1 | 0.08 | 1 | 64 |
| impulse-onto-battlefield | impulse-onto-battlefield |  | 1 | 0.08 | 1 | 126 |
| impulse-permanent | impulse-permanent |  | 1 | 0.08 | 1 | 40 |
| impulse-to-top | impulse-to-top |  | 1 | 0.08 | 1 | 14 |
| impulsive-mill | impulsive mill |  | 1 | 0.08 | 1 | 5 |
| infusion | infusion |  | 1 | 0.08 | 1 | 44 |
| inscryption-achievement | inscryption achievement |  | 1 | 0.08 | 1 | 40 |
| instant-speed-discard | instant speed discard |  | 1 | 0.08 | 1 | 22 |
| instant-sorcery-dichotomous | instant-sorcery-dichotomous |  | 1 | 0.08 | 1 | 16 |
| interrupt | interrupt |  | 1 | 0.08 | 1 | 52 |
| invitational-card | invitational card |  | 1 | 0.08 | 1 | 11 |
| keyword-errata-flash | keyword errata flash |  | 1 | 0.08 | 1 | 60 |
| keyword-errata-scry | keyword errata scry |  | 1 | 0.08 | 1 | 3 |
| land-or-hand | land or hand |  | 1 | 0.08 | 1 | 17 |
| landfall-other | landfall other |  | 1 | 0.08 | 1 | 30 |
| lands-in-graveyard-matter | lands in graveyard matter |  | 1 | 0.08 | 1 | 29 |
| lifegain-increaser | lifegain increaser |  | 1 | 0.08 | 1 | 15 |
| lure-limited | lure-limited |  | 1 | 0.08 | 1 | 48 |
| mana-ability-with-extra-effect | mana ability with extra effect |  | 1 | 0.08 | 1 | 64 |
| mana-dork-egg | mana dork egg |  | 1 | 0.08 | 1 | 32 |
| mana-gorger | mana gorger |  | 1 | 0.08 | 1 | 19 |
| mana-leak-series | mana leak series |  | 1 | 0.08 | 1 | 4 |
| mana-storage | mana storage |  | 1 | 0.08 | 1 | 81 |
| marauder | marauder |  | 1 | 0.08 | 1 | 19 |
| mass-land-denial | mass land denial |  | 1 | 0.08 | 1 | 113 |
| mass-regrowth | mass regrowth |  | 1 | 0.08 | 1 | 26 |
| mill-each | mill-each |  | 1 | 0.08 | 1 | 61 |
| mill-exile | mill-exile |  | 1 | 0.08 | 1 | 161 |
| minigame | minigame |  | 1 | 0.08 | 1 | 104 |
| multi-character-card | multi character card |  | 1 | 0.08 | 1 | 147 |
| multi-copy | multi-copy | multiple-clone | 1 | 0.08 | 1 | 94 |
| multiple-species-types | multiple species types |  | 1 | 0.08 | 1 | 96 |
| nightveil-theft | nightveil theft |  | 1 | 0.08 | 1 | 119 |
| nonbasic-basic-land-type | nonbasic-basic-land-type |  | 1 | 0.08 | 1 | 110 |
| noncreature-french-vanilla | noncreature french vanilla |  | 1 | 0.08 | 1 | 18 |
| notorious-templating | notorious templating |  | 1 | 0.08 | 1 | 77 |
| offcolor-additional-cost | offcolor additional cost | offcolor kicker | 1 | 0.08 | 1 | 82 |
| offcolor-mana-generation | offcolor mana generation |  | 1 | 0.08 | 1 | 20 |
| old-blocking-deathtouch | old blocking deathtouch |  | 1 | 0.08 | 1 | 35 |
| opponent-land-count-matters | opponent land count matters |  | 1 | 0.08 | 1 | 49 |
| opponent-discard-matters | opponent-discard matters | synergy-discard-opponent | 1 | 0.08 | 1 | 34 |
| orochi-ability | orochi ability |  | 1 | 0.08 | 1 | 10 |
| paradox | paradox | synergy-nonhand-cast | 1 | 0.08 | 1 | 45 |
| perpetual-aura | perpetual aura |  | 1 | 0.08 | 1 | 31 |
| pillage-effect | pillage effect |  | 1 | 0.08 | 1 | 12 |
| play-from-top | play from top | cast from top | 1 | 0.08 | 0 | 80 |
| poison-opponents | poison opponents |  | 1 | 0.08 | 1 | 21 |
| potentially-free | potentially free |  | 1 | 0.08 | 1 | 74 |
| power-matters-total | power matters-total |  | 1 | 0.08 | 0 | 64 |
| precognition | precognition |  | 1 | 0.08 | 0 | 61 |
| precognition-engine | precognition engine |  | 1 | 0.08 | 1 | 54 |
| protects-artifact | protects-artifact |  | 1 | 0.08 | 1 | 67 |
| protects-enchantment | protects-enchantment |  | 1 | 0.08 | 1 | 35 |
| protects-land | protects-land |  | 1 | 0.08 | 1 | 36 |
| pseudo-exert | pseudo-exert |  | 1 | 0.08 | 1 | 17 |
| pseudo-hexproof | pseudo-hexproof |  | 1 | 0.08 | 1 | 9 |
| pseudo-shroud | pseudo-shroud |  | 1 | 0.08 | 1 | 20 |
| rack-effect | rack effect |  | 1 | 0.08 | 1 | 16 |
| rainbow-land | rainbow land |  | 1 | 0.08 | 1 | 118 |
| reanimate-matters | reanimate matters |  | 1 | 0.08 | 1 | 22 |
| reanimate-land | reanimate-land |  | 1 | 0.08 | 1 | 73 |
| recursion-from-exile | recursion from exile |  | 1 | 0.08 | 1 | 22 |
| recursion-any | recursion-any |  | 1 | 0.08 | 0 | 80 |
| recursion-enchantment | recursion-enchantment |  | 1 | 0.08 | 0 | 81 |
| recycle | recycle | recycling | 1 | 0.08 | 1 | 77 |
| references-keyword | references keyword | references mechanic | 1 | 0.08 | 1 | 51 |
| regrowth-any | regrowth-any |  | 1 | 0.08 | 1 | 53 |
| regrowth-enchantment | regrowth-enchantment |  | 1 | 0.08 | 1 | 44 |
| repeatable-food | repeatable food |  | 1 | 0.08 | 1 | 67 |
| repeated-effect | repeated effect |  | 1 | 0.08 | 0 | 97 |
| repeated-keyword | repeated keyword | double keyword | 1 | 0.08 | 1 | 93 |
| restock-artifact | restock-artifact |  | 1 | 0.08 | 1 | 8 |
| restock-creature | restock-creature |  | 1 | 0.08 | 1 | 39 |
| restricted-attacker | restricted attacker |  | 1 | 0.08 | 1 | 116 |
| reveal-hand | reveal hand |  | 1 | 0.08 | 1 | 15 |
| rupture-spire | rupture spire |  | 1 | 0.08 | 1 | 7 |
| sacrifice-matters | sacrifice matters | synergy-sacrifice;thank you for your sacrifice | 1 | 0.08 | 0 | 140 |
| sacrifice-outlet-enchantment | sacrifice outlet-enchantment | sac outlet-enchantment | 1 | 0.08 | 0 | 135 |
| sacrifice-outlet-universal | sacrifice outlet-universal | sacrifice outlet-permanent;sac outlet-universal;sac outlet-permanent | 1 | 0.08 | 1 | 53 |
| scales-with-multiple | scales with multiple |  | 1 | 0.08 | 1 | 70 |
| second-draw-matters | second draw matters | seek out | 1 | 0.08 | 1 | 82 |
| self-life-loss-matters | self life loss matters |  | 1 | 0.08 | 1 | 37 |
| set-life-total | set life total |  | 1 | 0.08 | 1 | 65 |
| shakedown | shakedown |  | 1 | 0.08 | 1 | 5 |
| sift | sift |  | 1 | 0.08 | 1 | 17 |
| single-minded-graveyard-hate | single-minded graveyard hate |  | 1 | 0.08 | 1 | 16 |
| sneak-from-library | sneak from library |  | 1 | 0.08 | 0 | 220 |
| sneak-creature | sneak-creature |  | 1 | 0.08 | 1 | 99 |
| sneak-self | sneak-self |  | 1 | 0.08 | 1 | 54 |
| sneaky-self-trigger | sneaky-self-trigger |  | 1 | 0.08 | 1 | 30 |
| soothsaying | soothsaying |  | 1 | 0.08 | 1 | 37 |
| soul-warden-ability | soul warden ability | soul sister | 1 | 0.08 | 1 | 57 |
| spite-damage | spite damage |  | 1 | 0.08 | 1 | 36 |
| sports-name | sports name |  | 1 | 0.08 | 1 | 18 |
| stalking | stalking |  | 1 | 0.08 | 1 | 28 |
| strive | strive |  | 1 | 0.08 | 1 | 97 |
| sunder | sunder |  | 1 | 0.08 | 1 | 17 |
| super-pridemate | super-pridemate | sunbond;ageless entity;cradle of vitality | 1 | 0.08 | 1 | 10 |
| supercycle-mmmm-enrager | supercycle-mmmm-enrager | cycle-mmmm-enrager;cycle-obliterator;cycle-phyrexian-er | 1 | 0.08 | 1 | 4 |
| synergy-artifact-creature | synergy-artifact-creature |  | 1 | 0.08 | 1 | 177 |
| synergy-black | synergy-black | lord-black;black lord | 1 | 0.08 | 1 | 182 |
| synergy-bounce | synergy-bounce |  | 1 | 0.08 | 1 | 13 |
| synergy-color-every | synergy-color-every | synergy-five-colors | 1 | 0.08 | 1 | 9 |
| synergy-commander | synergy-commander |  | 1 | 0.08 | 1 | 199 |
| synergy-deathtouch | synergy-deathtouch |  | 1 | 0.08 | 1 | 30 |
| synergy-defender | synergy-defender |  | 1 | 0.08 | 1 | 24 |
| synergy-enchantment | synergy-enchantment |  | 1 | 0.08 | 1 | 268 |
| synergy-exile-cast | synergy-exile-cast |  | 1 | 0.08 | 0 | 77 |
| synergy-flash | synergy-flash |  | 1 | 0.08 | 1 | 10 |
| synergy-flashback | synergy-flashback |  | 1 | 0.08 | 1 | 13 |
| synergy-infect | synergy-infect |  | 1 | 0.08 | 1 | 2 |
| synergy-islandwalk | synergy-islandwalk |  | 1 | 0.08 | 1 | 2 |
| synergy-kicker | synergy-kicker |  | 1 | 0.08 | 1 | 15 |
| synergy-library-cast | synergy-library-cast |  | 1 | 0.08 | 0 | 49 |
| synergy-mill | synergy-mill |  | 1 | 0.08 | 1 | 98 |
| synergy-pw-jace | synergy-pw-jace | typal-jace | 1 | 0.08 | 1 | 11 |
| synergy-pw-specific | synergy-pw-specific |  | 1 | 0.08 | 0 | 70 |
| synergy-sacrifice-self | synergy-sacrifice-self | wants to be sacrificed | 1 | 0.08 | 1 | 15 |
| synergy-tapped | synergy-tapped |  | 1 | 0.08 | 1 | 52 |
| synergy-target | synergy-target |  | 1 | 0.08 | 0 | 188 |
| synergy-token | synergy-token |  | 1 | 0.08 | 0 | 240 |
| synergy-token-creature | synergy-token-creature |  | 1 | 0.08 | 1 | 113 |
| synergy-trample | synergy-trample |  | 1 | 0.08 | 1 | 30 |
| tapland-with-set's-mechanic | tapland with set's mechanic | tapland with set mechanic | 1 | 0.08 | 1 | 82 |
| tax-attack | tax attack |  | 1 | 0.08 | 1 | 42 |
| text-change | text change |  | 1 | 0.08 | 0 | 48 |
| theft-cast | theft-cast |  | 1 | 0.08 | 1 | 214 |
| theft-permanent | theft-permanent |  | 1 | 0.08 | 1 | 36 |
| three-letter-name | three-letter name |  | 1 | 0.08 | 1 | 28 |
| titan-immortality | titan immortality |  | 1 | 0.08 | 1 | 18 |
| tongue-twister | tongue twister |  | 1 | 0.08 | 1 | 9 |
| top-matters | top matters |  | 1 | 0.08 | 1 | 92 |
| torment | torment |  | 1 | 0.08 | 1 | 17 |
| transferrable-aura | transferrable aura |  | 1 | 0.08 | 1 | 22 |
| trigger-doubler | trigger doubler |  | 1 | 0.08 | 1 | 47 |
| turn-control | turn control | mindslaver | 1 | 0.08 | 1 | 11 |
| turns-off-defender-self | turns off defender-self |  | 1 | 0.08 | 1 | 74 |
| tutor-artifact-equipment | tutor-artifact-equipment | tutor-equipment | 1 | 0.08 | 1 | 22 |
| tutor-copy | tutor-copy |  | 1 | 0.08 | 1 | 18 |
| tutor-enchantment | tutor-enchantment |  | 1 | 0.08 | 0 | 38 |
| tutor-enchantment-aura | tutor-enchantment-aura | tutor-aura | 1 | 0.08 | 1 | 17 |
| tutor-flash | tutor-flash |  | 1 | 0.08 | 1 | 2 |
| tutor-land-basic-forest | tutor-land-basic-forest |  | 1 | 0.08 | 1 | 27 |
| tutor-land-basic-island | tutor-land-basic-island |  | 1 | 0.08 | 1 | 16 |
| tutor-permanent | tutor-permanent |  | 1 | 0.08 | 1 | 7 |
| typal-angel | typal-angel | tribal-angel | 1 | 0.08 | 1 | 24 |
| typal-assembly-worker | typal-assembly-worker | tribal-assembly-worker | 1 | 0.08 | 1 | 6 |
| typal-cat | typal-cat | tribal-cat | 1 | 0.08 | 1 | 24 |
| typal-exclusion | typal-exclusion |  | 1 | 0.08 | 0 | 39 |
| typal-giant | typal-giant | tribal-giant;giant tribal | 1 | 0.08 | 1 | 34 |
| typal-goat | typal-goat | tribal-goat | 1 | 0.08 | 1 | 5 |
| typal-griffin | typal-griffin | tribal-griffin | 1 | 0.08 | 1 | 5 |
| typal-non-human | typal-non-human | tribal-non-human | 1 | 0.08 | 1 | 29 |
| typal-share | typal-share | tribal-share | 1 | 0.08 | 1 | 77 |
| typal-thopter | typal-thopter | tribal-thopter | 1 | 0.08 | 1 | 8 |
| typal-treefolk | typal-treefolk | tribal-treefolk | 1 | 0.08 | 1 | 25 |
| typal-werewolf | typal-werewolf | tribal-werewolf | 1 | 0.08 | 1 | 32 |
| typal-wizard | typal-wizard | tribal-wizard | 1 | 0.08 | 1 | 126 |
| typal-zombie | typal-zombie | zombie lord;tribal-zombie | 1 | 0.08 | 1 | 125 |
| type-addition-book | type addition book |  | 1 | 0.08 | 1 | 46 |
| type-errata-egg | type errata egg |  | 1 | 0.08 | 1 | 5 |
| type-errata-lion | type errata lion |  | 1 | 0.08 | 1 | 3 |
| type-errata-naga | type errata naga |  | 1 | 0.08 | 1 | 40 |
| type-errata-name-self | type errata name self |  | 1 | 0.08 | 1 | 69 |
| type-errata-specific-elemental | type errata specific elemental |  | 1 | 0.08 | 1 | 10 |
| type-errata-specific-fish | type errata specific fish |  | 1 | 0.08 | 1 | 5 |
| type-errata-tiger | type errata tiger |  | 1 | 0.08 | 1 | 4 |
| undergrowth-all | undergrowth-all |  | 1 | 0.08 | 1 | 10 |
| unexile | unexile |  | 1 | 0.08 | 0 | 547 |
| unique-counter | unique counter |  | 1 | 0.08 | 1 | 150 |
| unique-evasion | unique evasion |  | 1 | 0.08 | 1 | 51 |
| unique-protection | unique protection |  | 1 | 0.08 | 1 | 44 |
| universal-type-change | universal type change |  | 1 | 0.08 | 1 | 112 |
| untapped-matters-self | untapped matters-self |  | 1 | 0.08 | 1 | 33 |
| untapper-permanent | untapper-permanent |  | 1 | 0.08 | 1 | 78 |
| useless-in-singleton-formats | useless in singleton formats |  | 1 | 0.08 | 1 | 25 |
| vanilla-equipment | vanilla equipment |  | 1 | 0.08 | 1 | 36 |
| vanity-card | vanity card |  | 1 | 0.08 | 1 | 167 |
| wheel-one-sided | wheel-one-sided |  | 1 | 0.08 | 1 | 108 |
| wheel-symmetrical | wheel-symmetrical |  | 1 | 0.08 | 1 | 53 |
| white-effect | white effect |  | 1 | 0.08 | 0 | 64 |
| 40k-model | 40k model |  | 0 | 0.0 | 0 | 128 |
| 5c-set-mechanic-commander | 5c set mechanic commander |  | 0 | 0.0 | 0 | 36 |
| absorb | absorb |  | 0 | 0.0 | 0 | 24 |
| activate-from-command-zone | activate from command zone |  | 0 | 0.0 | 0 | 3 |
| activate-from-exile | activate from exile |  | 0 | 0.0 | 0 | 5 |
| activate-from-stack | activate from stack |  | 0 | 0.0 | 0 | 3 |
| addendum | addendum |  | 0 | 0.0 | 0 | 17 |
| affinity-for-allies | affinity for allies |  | 0 | 0.0 | 0 | 1 |
| affinity-for-attacking | affinity for attacking |  | 0 | 0.0 | 0 | 10 |
| affinity-for-birds | affinity for birds |  | 0 | 0.0 | 0 | 1 |
| affinity-for-cats | affinity for cats |  | 0 | 0.0 | 0 | 1 |
| affinity-for-caves | affinity for caves |  | 0 | 0.0 | 0 | 1 |
| affinity-for-citizens | affinity for citizens |  | 0 | 0.0 | 0 | 1 |
| affinity-for-creature-type | affinity for creature type |  | 0 | 0.0 | 0 | 27 |
| affinity-for-creatures | affinity for creatures |  | 0 | 0.0 | 0 | 7 |
| affinity-for-daleks | affinity for daleks |  | 0 | 0.0 | 0 | 1 |
| affinity-for-devotion | affinity for devotion |  | 0 | 0.0 | 0 | 3 |
| affinity-for-domain | affinity for domain |  | 0 | 0.0 | 0 | 5 |
| affinity-for-elves | affinity for elves |  | 0 | 0.0 | 0 | 1 |
| affinity-for-enchantments | affinity for enchantments |  | 0 | 0.0 | 0 | 2 |
| affinity-for-equipment | affinity for equipment |  | 0 | 0.0 | 0 | 4 |
| affinity-for-humans | affinity for humans |  | 0 | 0.0 | 0 | 1 |
| affinity-for-knights | affinity for knights |  | 0 | 0.0 | 0 | 1 |
| affinity-for-outlaws | affinity for outlaws |  | 0 | 0.0 | 0 | 1 |
| affinity-for-party | affinity for party |  | 0 | 0.0 | 0 | 10 |
| affinity-for-phyrexians | affinity for phyrexians |  | 0 | 0.0 | 0 | 1 |
| affinity-for-slivers | affinity for slivers |  | 0 | 0.0 | 0 | 1 |
| affinity-for-spirits | affinity for spirits |  | 0 | 0.0 | 0 | 1 |
| affinity-for-tokens | affinity for tokens |  | 0 | 0.0 | 0 | 1 |
| affinity-for-towns | affinity for towns |  | 0 | 0.0 | 0 | 1 |
| affinity-undergrowth | affinity undergrowth | undergrowth affinity | 0 | 0.0 | 0 | 13 |
| age-matters | age matters |  | 0 | 0.0 | 0 | 3 |
| alternate-cost-gain-life | alternate-cost-gain-life |  | 0 | 0.0 | 0 | 3 |
| alternate-cost-life | alternate-cost-life |  | 0 | 0.0 | 0 | 48 |
| alternate-cost-sacrifice | alternate-cost-sacrifice |  | 0 | 0.0 | 0 | 57 |
| alternative-crewing | alternative crewing |  | 0 | 0.0 | 0 | 20 |
| animate-artifact | animate artifact |  | 0 | 0.0 | 0 | 77 |
| animate-battle | animate battle |  | 0 | 0.0 | 0 | 3 |
| animate-dead-like | animate dead-like |  | 0 | 0.0 | 0 | 7 |
| animate-enchantment | animate enchantment |  | 0 | 0.0 | 0 | 13 |
| animate-instant | animate instant |  | 0 | 0.0 | 0 | 3 |
| animate-planeswalker | animate planeswalker |  | 0 | 0.0 | 0 | 9 |
| animate-sorcery | animate sorcery |  | 0 | 0.0 | 0 | 3 |
| animate-token | animate token |  | 0 | 0.0 | 0 | 2 |
| animate-vehicle | animate vehicle |  | 0 | 0.0 | 0 | 17 |
| anime | anime |  | 0 | 0.0 | 0 | 1 |
| ante-matters | ante matters |  | 0 | 0.0 | 0 | 9 |
| any-player-ability | any player ability |  | 0 | 0.0 | 0 | 42 |
| any-zone-color-change | any zone color change |  | 0 | 0.0 | 0 | 3 |
| any-zone-type-change | any zone type change |  | 0 | 0.0 | 0 | 9 |
| arena-effect | arena effect |  | 0 | 0.0 | 0 | 3 |
| art-matters | art matters |  | 0 | 0.0 | 0 | 36 |
| artist-matters | artist matters |  | 0 | 0.0 | 0 | 20 |
| attacking-matters-any | attacking matters-any |  | 0 | 0.0 | 0 | 22 |
| attacking-opponents-matters | attacking opponents matters |  | 0 | 0.0 | 0 | 29 |
| auraify | auraify | becomes aura | 0 | 0.0 | 0 | 64 |
| awaken | awaken |  | 0 | 0.0 | 0 | 15 |
| bablovian-faction-leader | bablovian faction leader |  | 0 | 0.0 | 0 | 8 |
| balance | balance |  | 0 | 0.0 | 0 | 5 |
| banish-graveyard | banish-graveyard |  | 0 | 0.0 | 0 | 8 |
| banish-hand | banish-hand |  | 0 | 0.0 | 0 | 13 |
| banish-spell | banish-spell |  | 0 | 0.0 | 0 | 2 |
| battalion | battalion |  | 0 | 0.0 | 0 | 26 |
| becomes-changeling | becomes changeling |  | 0 | 0.0 | 0 | 5 |
| bid | bid |  | 0 | 0.0 | 0 | 4 |
| birthing-pod | birthing pod |  | 0 | 0.0 | 0 | 16 |
| block-when-tapped | block when tapped |  | 0 | 0.0 | 0 | 2 |
| block-without-creature | block without creature |  | 0 | 0.0 | 0 | 5 |
| blood-moon-effect | blood moon effect |  | 0 | 0.0 | 0 | 20 |
| board-reset | board-reset |  | 0 | 0.0 | 0 | 7 |
| boltland | boltland |  | 0 | 0.0 | 0 | 16 |
| booster-tutor | booster tutor |  | 0 | 0.0 | 0 | 14 |
| border-color-matters | border color matters |  | 0 | 0.0 | 0 | 9 |
| borrow-ability | borrow ability | share ability | 0 | 0.0 | 0 | 25 |
| bottom-of-library-matters | bottom of library matters |  | 0 | 0.0 | 0 | 12 |
| bounceable-aura | bounceable aura |  | 0 | 0.0 | 0 | 24 |
| bounty | bounty |  | 0 | 0.0 | 0 | 12 |
| brainstorm | brainstorm |  | 0 | 0.0 | 0 | 16 |
| breaks-ktk-morph-rule | breaks-ktk-morph-rule |  | 0 | 0.0 | 0 | 35 |
| bribery | bribery |  | 0 | 0.0 | 0 | 34 |
| bring-your-own-crew | bring your own crew | bring your own pilot | 0 | 0.0 | 0 | 37 |
| buff-pact | buff pact |  | 0 | 0.0 | 0 | 9 |
| bushido | bushido |  | 0 | 0.0 | 0 | 44 |
| buttcrew | buttcrew |  | 0 | 0.0 | 0 | 2 |
| buttfight | buttfight |  | 0 | 0.0 | 0 | 4 |
| buttfling | buttfling |  | 0 | 0.0 | 0 | 1 |
| buttlink | buttlink |  | 0 | 0.0 | 0 | 1 |
| buttsaddle | buttsaddle |  | 0 | 0.0 | 0 | 1 |
| buttstation | buttstation |  | 0 | 0.0 | 0 | 1 |
| card-game-reference | card game reference |  | 0 | 0.0 | 0 | 5 |
| card-style-matters | card style matters |  | 0 | 0.0 | 0 | 5 |
| card-types-in-graveyard-matter | card types in graveyard matter |  | 0 | 0.0 | 0 | 106 |
| card-types-matter | card types matter |  | 0 | 0.0 | 0 | 125 |
| cards-in-exile-matter | cards in exile matter |  | 0 | 0.0 | 0 | 22 |
| cast-tax | cast tax |  | 0 | 0.0 | 0 | 17 |
| castable-from-exile | castable from exile |  | 0 | 0.0 | 0 | 496 |
| castable-from-library | castable from library |  | 0 | 0.0 | 0 | 5 |
| cda-color | cda-color |  | 0 | 0.0 | 0 | 146 |
| chain-spell | chain spell |  | 0 | 0.0 | 0 | 9 |
| checklist-card | checklist card |  | 0 | 0.0 | 0 | 8 |
| clash-like | clash-like |  | 0 | 0.0 | 0 | 38 |
| clone-assassin | clone assassin |  | 0 | 0.0 | 0 | 3 |
| clone-graveyard | clone graveyard |  | 0 | 0.0 | 0 | 9 |
| clothing-matters | clothing matters |  | 0 | 0.0 | 0 | 10 |
| coin-flips-matter | coin flips matter |  | 0 | 0.0 | 0 | 13 |
| collector-number-matters | collector number matters |  | 0 | 0.0 | 0 | 4 |
| color-count-matters | color count matters |  | 0 | 0.0 | 0 | 7 |
| color-ward | color ward |  | 0 | 0.0 | 0 | 20 |
| color-choose-land | color-choose-land |  | 0 | 0.0 | 0 | 28 |
| combat-arbiter | combat arbiter |  | 0 | 0.0 | 0 | 11 |
| combat-timing-restriction | combat timing restriction |  | 0 | 0.0 | 0 | 42 |
| commander-set-booster-cards | commander set booster cards |  | 0 | 0.0 | 0 | 100 |
| commander-tax-evasion | commander tax evasion |  | 0 | 0.0 | 0 | 11 |
| commander-tax-matters | commander tax matters |  | 0 | 0.0 | 0 | 17 |
| commander-lord | commander-lord |  | 0 | 0.0 | 0 | 5 |
| conditional-aura | conditional aura |  | 0 | 0.0 | 0 | 15 |
| confluence | confluence | modal-3/3 | 0 | 0.0 | 0 | 14 |
| conjure | conjure |  | 0 | 0.0 | 0 | 208 |
| conjure-artifact | conjure-artifact |  | 0 | 0.0 | 0 | 24 |
| conjure-artifact-creature | conjure-artifact-creature |  | 0 | 0.0 | 0 | 8 |
| conjure-battle | conjure-battle |  | 0 | 0.0 | 0 | 2 |
| conjure-card | conjure-card |  | 0 | 0.0 | 0 | 11 |
| conjure-creature | conjure-creature |  | 0 | 0.0 | 0 | 101 |
| conjure-duplicate | conjure-duplicate |  | 0 | 0.0 | 0 | 72 |
| conjure-enchantment | conjure-enchantment |  | 0 | 0.0 | 0 | 17 |
| conjure-instant | conjure-instant |  | 0 | 0.0 | 0 | 20 |
| conjure-land | conjure-land |  | 0 | 0.0 | 0 | 16 |
| conjure-named | conjure-named |  | 0 | 0.0 | 0 | 102 |
| conjure-nonland | conjure-nonland |  | 0 | 0.0 | 0 | 1 |
| conjure-permanent | conjure-permanent |  | 0 | 0.0 | 0 | 1 |
| conjure-planeswalker | conjure-planeswalker |  | 0 | 0.0 | 0 | 5 |
| conjure-random | conjure-random |  | 0 | 0.0 | 0 | 25 |
| conjure-sorcery | conjure-sorcery |  | 0 | 0.0 | 0 | 17 |
| conjure-spellbook | conjure-spellbook |  | 0 | 0.0 | 0 | 22 |
| conjure-to-battlefield | conjure-to-battlefield |  | 0 | 0.0 | 0 | 62 |
| conjure-to-exile | conjure-to-exile |  | 0 | 0.0 | 0 | 7 |
| conjure-to-graveyard | conjure-to-graveyard | conjure-graveyard | 0 | 0.0 | 0 | 15 |
| conjure-to-hand | conjure-to-hand |  | 0 | 0.0 | 0 | 104 |
| conjure-to-library | conjure-to-library |  | 0 | 0.0 | 0 | 19 |
| consult-onto-battlefield | consult-onto-battlefield |  | 0 | 0.0 | 0 | 76 |
| continuous-effect-from-graveyard | continuous effect from graveyard | continuous effect in graveyard | 0 | 0.0 | 0 | 9 |
| control-attacker | control attacker |  | 0 | 0.0 | 0 | 8 |
| control-blocker | control blocker |  | 0 | 0.0 | 0 | 11 |
| converge | converge |  | 0 | 0.0 | 0 | 51 |
| copy-from-graveyard | copy from graveyard | reanimate copy | 0 | 0.0 | 0 | 73 |
| copy-artifact | copy-artifact |  | 0 | 0.0 | 0 | 106 |
| copy-aura | copy-aura |  | 0 | 0.0 | 0 | 37 |
| copy-enchantment | copy-enchantment |  | 0 | 0.0 | 0 | 49 |
| copy-equipment | copy-equipment |  | 0 | 0.0 | 0 | 30 |
| copy-land | copy-land |  | 0 | 0.0 | 0 | 37 |
| copy-legendary | copy-legendary | token-bypasses-legend-rule | 0 | 0.0 | 0 | 56 |
| copy-nonland | copy-nonland |  | 0 | 0.0 | 0 | 12 |
| copy-permanent | copy-permanent |  | 0 | 0.0 | 0 | 20 |
| copy-permanent-spell | copy-permanent-spell |  | 0 | 0.0 | 0 | 43 |
| copy-planeswalker | copy-planeswalker |  | 0 | 0.0 | 0 | 36 |
| cost-increaser | cost increaser |  | 0 | 0.0 | 0 | 76 |
| cost-reducer-activated-ability | cost-reducer-activated-ability |  | 0 | 0.0 | 0 | 46 |
| cost-reducer-artifact | cost-reducer-artifact |  | 0 | 0.0 | 0 | 30 |
| cost-reducer-aura | cost-reducer-aura |  | 0 | 0.0 | 0 | 5 |
| cost-reducer-battle | cost-reducer-battle |  | 0 | 0.0 | 0 | 1 |
| cost-reducer-colored-mana | cost-reducer-colored-mana |  | 0 | 0.0 | 0 | 21 |
| cost-reducer-enchantment | cost-reducer-enchantment |  | 0 | 0.0 | 0 | 18 |
| cost-reducer-equip-ability | cost-reducer-equip-ability |  | 0 | 0.0 | 0 | 22 |
| cost-reducer-equipment | cost-reducer-equipment |  | 0 | 0.0 | 0 | 7 |
| cost-reducer-historic | cost-reducer-historic |  | 0 | 0.0 | 0 | 2 |
| cost-reducer-legendary | cost-reducer-legendary |  | 0 | 0.0 | 0 | 5 |
| cost-reducer-lesson | cost-reducer-lesson |  | 0 | 0.0 | 0 | 1 |
| cost-reducer-noncreature | cost-reducer-noncreature |  | 0 | 0.0 | 0 | 11 |
| cost-reducer-nonland | cost-reducer-nonland |  | 0 | 0.0 | 0 | 4 |
| cost-reducer-planeswalker | cost-reducer-planeswalker |  | 0 | 0.0 | 0 | 7 |
| cost-reducer-saga | cost-reducer-saga |  | 0 | 0.0 | 0 | 2 |
| cost-reducer-vehicle | cost-reducer-vehicle |  | 0 | 0.0 | 0 | 1 |
| counter-fuel-energy | counter fuel-energy |  | 0 | 0.0 | 0 | 122 |
| counter-fuel-fade | counter fuel-fade |  | 0 | 0.0 | 0 | 9 |
| counter-fuel-keyword | counter fuel-keyword |  | 0 | 0.0 | 0 | 9 |
| counter-fuel-lore | counter fuel-lore |  | 0 | 0.0 | 0 | 1 |
| counter-fuel-loyalty | counter fuel-loyalty |  | 0 | 0.0 | 0 | 2 |
| counter-fuel-oil | counter fuel-oil |  | 0 | 0.0 | 0 | 25 |
| counter-fuel-other | counter fuel-other |  | 0 | 0.0 | 0 | 48 |
| counter-fuel-pt | counter fuel-pt |  | 0 | 0.0 | 0 | 1 |
| counter-fuel-shield | counter fuel-shield |  | 0 | 0.0 | 0 | 2 |
| counter-fuel-stun | counter fuel-stun |  | 0 | 0.0 | 0 | 1 |
| counter-fuel-time | counter fuel-time |  | 0 | 0.0 | 0 | 3 |
| counter-preservation | counter preservation |  | 0 | 0.0 | 0 | 12 |
| counter-preservation-self | counter preservation-self |  | 0 | 0.0 | 0 | 45 |
| counters-remain | counters remain |  | 0 | 0.0 | 0 | 2 |
| counterspell-ability | counterspell-ability | stifle | 0 | 0.0 | 0 | 52 |
| counterspell-aura | counterspell-aura |  | 0 | 0.0 | 0 | 3 |
| counterspell-automatic | counterspell-automatic |  | 0 | 0.0 | 0 | 38 |
| counterspell-battle | counterspell-battle |  | 0 | 0.0 | 0 | 1 |
| counterspell-bounce | counterspell-bounce |  | 0 | 0.0 | 0 | 17 |
| counterspell-enchantment | counterspell-enchantment |  | 0 | 0.0 | 0 | 10 |
| counterspell-exile | counterspell-exile |  | 0 | 0.0 | 0 | 42 |
| counterspell-loyalty-ability | counterspell-loyalty-ability |  | 0 | 0.0 | 0 | 1 |
| counterspell-planeswalker | counterspell-planeswalker |  | 0 | 0.0 | 0 | 8 |
| counterspell-reusable | counterspell-reusable | repeatable counterspell | 0 | 0.0 | 0 | 79 |
| counterspell-sweeper | counterspell-sweeper |  | 0 | 0.0 | 0 | 8 |
| counterspell-tuck | counterspell-tuck |  | 0 | 0.0 | 0 | 12 |
| counts-as-a-type | counts as a type |  | 0 | 0.0 | 0 | 25 |
| cover-card | cover card |  | 0 | 0.0 | 0 | 4 |
| cranial-plating | cranial plating |  | 0 | 0.0 | 0 | 50 |
| creates-oracle-copy | creates oracle copy |  | 0 | 0.0 | 0 | 6 |
| creates-oracle-token | creates oracle token | creates card token | 0 | 0.0 | 0 | 32 |
| creates-token-of-a-card | creates token of a card |  | 0 | 0.0 | 0 | 82 |
| creature-type-bodyguard | creature type bodyguard |  | 0 | 0.0 | 0 | 3 |
| creature-type-enchantress | creature type enchantress |  | 0 | 0.0 | 0 | 3 |
| creature-type-fungusaur | creature type fungusaur |  | 0 | 0.0 | 0 | 1 |
| creature-type-guardian | creature type guardian |  | 0 | 0.0 | 0 | 10 |
| creature-type-hero | creature type hero |  | 0 | 0.0 | 0 | 3 |
| creature-type-lycanthrope | creature type lycanthrope |  | 0 | 0.0 | 0 | 2 |
| creature-type-phantasm | creature type phantasm |  | 0 | 0.0 | 0 | 5 |
| creature-type-ship | creature type ship |  | 0 | 0.0 | 0 | 15 |
| creature-type-townsfolk | creature type townsfolk |  | 0 | 0.0 | 0 | 12 |
| creature-type-undead | creature type undead |  | 0 | 0.0 | 0 | 3 |
| creature-ability-noncreature | creature-ability-noncreature |  | 0 | 0.0 | 0 | 59 |
| crewless-vehicle | crewless vehicle |  | 0 | 0.0 | 0 | 21 |
| cross-game-card | cross-game card |  | 0 | 0.0 | 0 | 2 |
| crucible-of-worlds | crucible of worlds | crucible | 0 | 0.0 | 0 | 22 |
| cunning | cunning |  | 0 | 0.0 | 0 | 5 |
| cycle-1mv-tutor | cycle-1mv-tutor | cycle-1cmc-tutor | 0 | 0.0 | 0 | 5 |
| cycle-2x2-draft-signpost | cycle-2x2-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-2xm-draft-signpost | cycle-2xm-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-40k-alt-commander | cycle-40k-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-40k-face-commander | cycle-40k-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-40k-saga | cycle-40k-saga |  | 0 | 0.0 | 0 | 4 |
| cycle-5dn-bringer | cycle-5dn-bringer |  | 0 | 0.0 | 0 | 5 |
| cycle-5dn-mm-attach-equipment | cycle-5dn-mm-attach-equipment | cycle-mm-attach-equipment | 0 | 0.0 | 0 | 5 |
| cycle-5dn-station | cycle-5dn-station |  | 0 | 0.0 | 0 | 4 |
| cycle-a25-allied-enhanced | cycle-a25-allied-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-a25-r-two-color | cycle-a25-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-a25-same-name-enhanced | cycle-a25-same-name-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-a25-u-legend | cycle-a25-u-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-abu-dual-land | cycle-abu-dual-land | abu dual land | 0 | 0.0 | 0 | 10 |
| cycle-acr-auto-equip | cycle-acr-auto-equip |  | 0 | 0.0 | 0 | 5 |
| cycle-acr-saga | cycle-acr-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-aether-servo-creator | cycle-aer-aether-servo-creator |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-automaton | cycle-aer-automaton |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-draft-signpost | cycle-aer-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-aer-expertise | cycle-aer-expertise |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-implement | cycle-aer-implement |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-legend | cycle-aer-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-aer-precon-tutor | cycle-aer-precon-tutor |  | 0 | 0.0 | 0 | 2 |
| cycle-afc-alt-commander | cycle-afc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-afc-d20-spell | cycle-afc-d20-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-afc-endeavor | cycle-afc-endeavor |  | 0 | 0.0 | 0 | 5 |
| cycle-afc-face-commander | cycle-afc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-afr-chromatic-dragon | cycle-afr-chromatic-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-color-hate | cycle-afr-color-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-creatureland | cycle-afr-creatureland |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-m-dragon | cycle-afr-m-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-planeswalker | cycle-afr-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-u-class | cycle-afr-u-class |  | 0 | 0.0 | 0 | 5 |
| cycle-afr-u-legend | cycle-afr-u-legend | cycle-afr-draft-signpost | 0 | 0.0 | 0 | 10 |
| cycle-akh-allied-aftermath | cycle-akh-allied-aftermath |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-cartouche | cycle-akh-cartouche |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-cycle-effect | cycle-akh-cycle-effect |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-dual-cycling-land | cycle-akh-dual-cycling-land |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-enemy-aftermath | cycle-akh-enemy-aftermath |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-god | cycle-akh-god |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-monocolor-aftermath | cycle-akh-monocolor-aftermath |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-monument | cycle-akh-monument |  | 0 | 0.0 | 0 | 5 |
| cycle-akh-trial | cycle-akh-trial |  | 0 | 0.0 | 0 | 5 |
| cycle-ala-4mnno | cycle-ala-4mnno |  | 0 | 0.0 | 0 | 5 |
| cycle-ala-battlemage | cycle-ala-battlemage |  | 0 | 0.0 | 0 | 5 |
| cycle-ala-jund-scavenger | cycle-ala-jund-scavenger |  | 0 | 0.0 | 0 | 3 |
| cycle-ala-legend | cycle-ala-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-ala-naya-druid | cycle-ala-naya-druid |  | 0 | 0.0 | 0 | 3 |
| cycle-ala-r-tricolor | cycle-ala-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-all-enemy-hate | cycle-all-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-all-pitch-spell | cycle-all-pitch-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-all-r-tricolor | cycle-all-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-all-replacement-land | cycle-all-replacement-land |  | 0 | 0.0 | 0 | 5 |
| cycle-all-u-two-color | cycle-all-u-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-apc-bloodfire-vertical | cycle-apc-bloodfire-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-apc-disciple | cycle-apc-disciple |  | 0 | 0.0 | 0 | 5 |
| cycle-apc-envoy | cycle-apc-envoy |  | 0 | 0.0 | 0 | 7 |
| cycle-apc-painland | cycle-apc-painland |  | 0 | 0.0 | 0 | 5 |
| cycle-apc-penumbra-vertical | cycle-apc-penumbra-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-apc-r-tricolor | cycle-apc-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-apc-r-two-color | cycle-apc-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-apc-sanctuary | cycle-apc-sanctuary | cycle-sanctuary | 0 | 0.0 | 0 | 5 |
| cycle-apc-split-card | cycle-apc-split-card |  | 0 | 0.0 | 0 | 5 |
| cycle-apc-u-two-color | cycle-apc-u-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-apc-volver | cycle-apc-volver | cycle-volver | 0 | 0.0 | 0 | 5 |
| cycle-apc-whirlpool-vertical | cycle-apc-whirlpool-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-arb-hybrid-cycler | cycle-arb-hybrid-cycler |  | 0 | 0.0 | 0 | 5 |
| cycle-arb-legend | cycle-arb-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-arb-u-tricolor | cycle-arb-u-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-arch-charm | cycle-arch-charm |  | 0 | 0.0 | 0 | 3 |
| cycle-arn-djinn | cycle-arn-djinn |  | 0 | 0.0 | 0 | 4 |
| cycle-arn-efreet | cycle-arn-efreet |  | 0 | 0.0 | 0 | 4 |
| cycle-ascendancy | cycle-ascendancy |  | 0 | 0.0 | 0 | 10 |
| cycle-avr-legend-angel | cycle-avr-legend-angel |  | 0 | 0.0 | 0 | 4 |
| cycle-avr-r-miracle | cycle-avr-r-miracle |  | 0 | 0.0 | 0 | 4 |
| cycle-basic-snow-land | cycle-basic-snow-land |  | 0 | 0.0 | 0 | 6 |
| cycle-bbd-bond-land | cycle-bbd-bond-land |  | 0 | 0.0 | 0 | 5 |
| cycle-bbd-c-two-color | cycle-bbd-c-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-bbd-friend-foe | cycle-bbd-friend-foe |  | 0 | 0.0 | 0 | 5 |
| cycle-bbd-legendary-partner | cycle-bbd-legendary-partner |  | 0 | 0.0 | 0 | 10 |
| cycle-bbd-r-two-color | cycle-bbd-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-bbd-u-partner | cycle-bbd-u-partner |  | 0 | 0.0 | 0 | 10 |
| cycle-bfz-blighted-land | cycle-bfz-blighted-land |  | 0 | 0.0 | 0 | 5 |
| cycle-bfz-color-landfall | cycle-bfz-color-landfall |  | 0 | 0.0 | 0 | 5 |
| cycle-bfz-draft-signpost | cycle-bfz-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-bfz-landfall-2-2-pump | cycle-bfz-landfall-2-2-pump |  | 0 | 0.0 | 0 | 5 |
| cycle-bfz-retreat | cycle-bfz-retreat |  | 0 | 0.0 | 0 | 5 |
| cycle-bfz-tangoland | cycle-bfz-tangoland |  | 0 | 0.0 | 0 | 5 |
| cycle-bfz-utilityland | cycle-bfz-utilityland |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-c-gift | cycle-blb-c-gift |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-c-offspring | cycle-blb-c-offspring |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-c-typal-boost | cycle-blb-c-typal-boost |  | 0 | 0.0 | 0 | 10 |
| cycle-blb-draft-signpost | cycle-blb-draft-signpost | cycle-blb-mentor | 0 | 0.0 | 0 | 10 |
| cycle-blb-duo | cycle-blb-duo |  | 0 | 0.0 | 0 | 10 |
| cycle-blb-hybrid | cycle-blb-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-blb-m-mono-calamity | cycle-blb-m-mono-calamity |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-r-talent | cycle-blb-r-talent |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-r-two-color-legend | cycle-blb-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-blb-season | cycle-blb-season |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-u-offspring | cycle-blb-u-offspring |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-u-talent | cycle-blb-u-talent |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-u-typal | cycle-blb-u-typal |  | 0 | 0.0 | 0 | 10 |
| cycle-blb-valley-caller | cycle-blb-valley-caller |  | 0 | 0.0 | 0 | 5 |
| cycle-blb-village | cycle-blb-village |  | 0 | 0.0 | 0 | 5 |
| cycle-blc-alt-commander | cycle-blc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-blc-face-commander | cycle-blc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-blc-talent | cycle-blc-talent |  | 0 | 0.0 | 0 | 4 |
| cycle-block-bfz-creatureland | cycle-block-bfz-creatureland | cycle-bfz-manland | 0 | 0.0 | 0 | 5 |
| cycle-block-grn-c-guild-kw | cycle-block-grn-c-guild-kw |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-guild-champion | cycle-block-grn-guild-champion |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-guildmage | cycle-block-grn-guildmage |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-guildmaster | cycle-block-grn-guildmaster |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-hybrid-critter | cycle-block-grn-hybrid-critter |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-locket | cycle-block-grn-locket |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-mmnn | cycle-block-grn-mmnn |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-r-split | cycle-block-grn-r-split |  | 0 | 0.0 | 0 | 10 |
| cycle-block-grn-u-split | cycle-block-grn-u-split |  | 0 | 0.0 | 0 | 10 |
| cycle-block-inv-counterspell | cycle-block-inv-counterspell |  | 0 | 0.0 | 0 | 4 |
| cycle-block-rav-c-hybrid | cycle-block-rav-c-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-c-hybrid | cycle-block-rtr-c-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-guild-charm | cycle-block-rtr-guild-charm | cycle-gtc-guild-charm | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-guildmage | cycle-block-rtr-guildmage |  | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-m-multicolor | cycle-block-rtr-m-multicolor |  | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-r-hybrid | cycle-block-rtr-r-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-block-rtr-u-guild-kw | cycle-block-rtr-u-guild-kw |  | 0 | 0.0 | 0 | 10 |
| cycle-block-shm-c-h-1-drop | cycle-block-shm-c-h-1-drop |  | 0 | 0.0 | 0 | 10 |
| cycle-block-shm-u-h-3-drop | cycle-block-shm-u-h-3-drop |  | 0 | 0.0 | 0 | 10 |
| cycle-block-ths-minor-god | cycle-block-ths-minor-god |  | 0 | 0.0 | 0 | 10 |
| cycle-bng-archetype | cycle-bng-archetype |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-devotion-x | cycle-bng-devotion-x |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-draft-signpost | cycle-bng-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-bng-enemy-ability | cycle-bng-enemy-ability |  | 0 | 0.0 | 0 | 4 |
| cycle-bng-fated-spell | cycle-bng-fated-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-inspired-token | cycle-bng-inspired-token |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-minor-god | cycle-bng-minor-god |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-nyxborn | cycle-bng-nyxborn |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-tapping-aura | cycle-bng-tapping-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-u-bestow | cycle-bng-u-bestow |  | 0 | 0.0 | 0 | 5 |
| cycle-bng-u-tribute | cycle-bng-u-tribute |  | 0 | 0.0 | 0 | 5 |
| cycle-bok-baku | cycle-bok-baku |  | 0 | 0.0 | 0 | 5 |
| cycle-bok-genju | cycle-bok-genju |  | 0 | 0.0 | 0 | 6 |
| cycle-bok-glasskite-vertical | cycle-bok-glasskite-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-bok-kami-patron | cycle-bok-kami-patron |  | 0 | 0.0 | 0 | 5 |
| cycle-bok-m-sac-spirit | cycle-bok-m-sac-spirit |  | 0 | 0.0 | 0 | 5 |
| cycle-bok-nomana-splice-arcane | cycle-bok-nomana-splice-arcane |  | 0 | 0.0 | 0 | 5 |
| cycle-bok-shoal | cycle-bok-shoal | cycle-shoal | 0 | 0.0 | 0 | 5 |
| cycle-bondland | cycle-bondland | cycle-crowdland | 0 | 0.0 | 0 | 10 |
| cycle-bro-basic-land-count | cycle-bro-basic-land-count |  | 0 | 0.0 | 0 | 5 |
| cycle-bro-c-mulch | cycle-bro-c-mulch |  | 0 | 0.0 | 0 | 5 |
| cycle-bro-command | cycle-bro-command |  | 0 | 0.0 | 0 | 5 |
| cycle-bro-draft-signpost | cycle-bro-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-bro-m-color-artifact | cycle-bro-m-color-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-bro-meld | cycle-bro-meld |  | 0 | 0.0 | 0 | 3 |
| cycle-bro-mishra-vertical | cycle-bro-mishra-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-bro-tron-worker | cycle-bro-tron-worker |  | 0 | 0.0 | 0 | 3 |
| cycle-bro-urza-vertical | cycle-bro-urza-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-c13-alt-commander | cycle-c13-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c13-curse | cycle-c13-curse |  | 0 | 0.0 | 0 | 5 |
| cycle-c13-face-commander | cycle-c13-face-commander | cycle-c13-commander | 0 | 0.0 | 0 | 5 |
| cycle-c13-reprint-commander | cycle-c13-reprint-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c13-tempting-offer | cycle-c13-tempting-offer |  | 0 | 0.0 | 0 | 5 |
| cycle-c14-alt-commander | cycle-c14-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c14-historical-legend | cycle-c14-historical-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-c14-lieutenant | cycle-c14-lieutenant |  | 0 | 0.0 | 0 | 5 |
| cycle-c14-offering | cycle-c14-offering |  | 0 | 0.0 | 0 | 5 |
| cycle-c14-planeswalker | cycle-c14-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-c15-alt-commander | cycle-c15-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c15-commander-reference | cycle-c15-commander-reference |  | 0 | 0.0 | 0 | 5 |
| cycle-c15-confluence | cycle-c15-confluence |  | 0 | 0.0 | 0 | 5 |
| cycle-c15-experience-commander | cycle-c15-experience-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c15-myriad-creature | cycle-c15-myriad-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-c16-basic-landcycling | cycle-c16-basic-landcycling |  | 0 | 0.0 | 0 | 5 |
| cycle-c16-face-commander | cycle-c16-face-commander | cycle-c16-mnop-commander | 0 | 0.0 | 0 | 5 |
| cycle-c16-m-partner | cycle-c16-m-partner |  | 0 | 0.0 | 0 | 10 |
| cycle-c16-r-partner | cycle-c16-r-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-c16-u-monocolor | cycle-c16-u-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-c16-undaunted-spell | cycle-c16-undaunted-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-c17-curse | cycle-c17-curse |  | 0 | 0.0 | 0 | 5 |
| cycle-c17-eminence-commander | cycle-c17-eminence-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-c17-kindred-spell | cycle-c17-kindred-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-c18-alt-commander | cycle-c18-alt-commander |  | 0 | 0.0 | 0 | 8 |
| cycle-c18-commander-storm | cycle-c18-commander-storm | commander storm | 0 | 0.0 | 0 | 5 |
| cycle-c18-lieutenant | cycle-c18-lieutenant |  | 0 | 0.0 | 0 | 5 |
| cycle-c18-planeswalker | cycle-c18-planeswalker |  | 0 | 0.0 | 0 | 4 |
| cycle-c18-signature-spell | cycle-c18-signature-spell |  | 0 | 0.0 | 0 | 4 |
| cycle-c18-sub-commander | cycle-c18-sub-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-c19-alt-commander | cycle-c19-alt-commander |  | 0 | 0.0 | 0 | 8 |
| cycle-c19-face-commander | cycle-c19-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-c19-planeswalker | cycle-c19-planeswalker |  | 0 | 0.0 | 0 | 4 |
| cycle-c19-secondary-commander | cycle-c19-secondary-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-c19-signature-spell | cycle-c19-signature-spell |  | 0 | 0.0 | 0 | 4 |
| cycle-c20-alt-commander | cycle-c20-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-bonder-partner | cycle-c20-bonder-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-face-commander | cycle-c20-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-free-spell | cycle-c20-free-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-impetus | cycle-c20-impetus |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-monster-partner | cycle-c20-monster-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-c20-planeswalker | cycle-c20-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-c21-alt-commander | cycle-c21-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c21-college-spell | cycle-c21-college-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-c21-face-commander | cycle-c21-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-c21-mono-legend | cycle-c21-mono-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-c21-technique | cycle-c21-technique |  | 0 | 0.0 | 0 | 5 |
| cycle-cardinal-paladin | cycle-cardinal-paladin |  | 0 | 0.0 | 0 | 4 |
| cycle-checkland | cycle-checkland |  | 0 | 0.0 | 0 | 10 |
| cycle-chk-deceiver | cycle-chk-deceiver |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-dragon | cycle-chk-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-flash-aura | cycle-chk-flash-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-honden | cycle-chk-honden | cycle-chk-shrine | 0 | 0.0 | 0 | 5 |
| cycle-chk-legendary-land | cycle-chk-legendary-land |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-napland | cycle-chk-napland |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-r-flip | cycle-chk-r-flip |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-u-flip | cycle-chk-u-flip |  | 0 | 0.0 | 0 | 5 |
| cycle-chk-zubera | cycle-chk-zubera |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-adventurer | cycle-clb-adventurer |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-ancient-dragon | cycle-clb-ancient-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-back-enemy-legend | cycle-clb-back-enemy-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-backward-ally-legend | cycle-clb-backward-ally-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-c-background | cycle-clb-c-background |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-c-d20 | cycle-clb-c-d20 |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-dethrone-background | cycle-clb-dethrone-background |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-draft-signpost | cycle-clb-draft-signpost | cycle-clb-uncommon-legend | 0 | 0.0 | 0 | 10 |
| cycle-clb-face-commander | cycle-clb-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-clb-forward-ally-legend | cycle-clb-forward-ally-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-forward-enemy-legend | cycle-clb-forward-enemy-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-gem-dragon | cycle-clb-gem-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-god | cycle-clb-god |  | 0 | 0.0 | 0 | 3 |
| cycle-clb-invoker | cycle-clb-invoker | cycle-clb-8-mana-ability | 0 | 0.0 | 0 | 5 |
| cycle-clb-legend-spell | cycle-clb-legend-spell | cycle-clb-legend's-roll | 0 | 0.0 | 0 | 5 |
| cycle-clb-orb-of-dragonkind | cycle-clb-orb-of-dragonkind |  | 0 | 0.0 | 0 | 3 |
| cycle-clb-precon-background | cycle-clb-precon-background |  | 0 | 0.0 | 0 | 4 |
| cycle-clb-r-background | cycle-clb-r-background |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-r-mono-legend | cycle-clb-r-mono-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-r-two-color-legend | cycle-clb-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-clb-thriving-gate | cycle-clb-thriving-gate |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-tricolor-legend | cycle-clb-tricolor-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-clb-u-background | cycle-clb-u-background |  | 0 | 0.0 | 0 | 10 |
| cycle-clb-u-d20 | cycle-clb-u-d20 |  | 0 | 0.0 | 0 | 5 |
| cycle-clb-u-initiative | cycle-clb-u-initiative |  | 0 | 0.0 | 0 | 5 |
| cycle-clu-clue-equipment | cycle-clu-clue-equipment | cycle-mkm-clue-equipment | 0 | 0.0 | 0 | 5 |
| cycle-clu-guild-rare | cycle-clu-guild-rare |  | 0 | 0.0 | 0 | 10 |
| cycle-clu-r-hybrid | cycle-clu-r-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-clu-suspect | cycle-clu-suspect |  | 0 | 0.0 | 0 | 6 |
| cycle-clu-unc-hybrid | cycle-clu-unc-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-cmb1-dual-land | cycle-cmb1-dual-land |  | 0 | 0.0 | 0 | 5 |
| cycle-cmd-alt-commander | cycle-cmd-alt-commander | cycle-cmd-wedge-alt-commander | 0 | 0.0 | 0 | 5 |
| cycle-cmd-enemy-legend | cycle-cmd-enemy-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-cmd-face-commander | cycle-cmd-face-commander | cycle-cmd-wedge-commander | 0 | 0.0 | 0 | 5 |
| cycle-cmd-join-forces | cycle-cmd-join-forces |  | 0 | 0.0 | 0 | 5 |
| cycle-cmd-vow | cycle-cmd-vow |  | 0 | 0.0 | 0 | 5 |
| cycle-cmm-alt-commander | cycle-cmm-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-cmm-face-commander | cycle-cmm-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-cmm-m-mono-legend | cycle-cmm-m-mono-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-cmm-r-two-color-legend | cycle-cmm-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-cmm-sliver | cycle-cmm-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-cmm-tricolor-legend | cycle-cmm-tricolor-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-cmr-artifact-partner | cycle-cmr-artifact-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-backward-partner | cycle-cmr-backward-partner |  | 0 | 0.0 | 0 | 10 |
| cycle-cmr-bond-land | cycle-cmr-bond-land |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-court | cycle-cmr-court |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-draft-signpost | cycle-cmr-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-cmr-face-commander | cycle-cmr-face-commander |  | 0 | 0.0 | 0 | 2 |
| cycle-cmr-familiar | cycle-cmr-familiar |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-m-partner | cycle-cmr-m-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-m-sorcery | cycle-cmr-m-sorcery |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-r-partner | cycle-cmr-r-partner |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-r-two-color | cycle-cmr-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-cmr-tricolor-legend | cycle-cmr-tricolor-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-cmr-vow | cycle-cmr-vow |  | 0 | 0.0 | 0 | 5 |
| cycle-cmr-will | cycle-cmr-will |  | 0 | 0.0 | 0 | 5 |
| cycle-cn2-c-draft | cycle-cn2-c-draft |  | 0 | 0.0 | 0 | 5 |
| cycle-cn2-color-conspiracy | cycle-cn2-color-conspiracy |  | 0 | 0.0 | 0 | 5 |
| cycle-cn2-draft-signpost | cycle-cn2-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-cn2-r-draft | cycle-cn2-r-draft |  | 0 | 0.0 | 0 | 5 |
| cycle-cn2-r-monarch | cycle-cn2-r-monarch |  | 0 | 0.0 | 0 | 5 |
| cycle-cn2-u-draft | cycle-cn2-u-draft |  | 0 | 0.0 | 0 | 5 |
| cycle-cns-m-monocolor | cycle-cns-m-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-cns-pp-counter-recycler | cycle-cns-pp-counter-recycler |  | 0 | 0.0 | 0 | 5 |
| cycle-cns-r-two-color | cycle-cns-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-con-backward-synergy | cycle-con-backward-synergy |  | 0 | 0.0 | 0 | 5 |
| cycle-con-c-domain-spell | cycle-con-c-domain-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-con-c-two-color | cycle-con-c-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-con-esper-scepter | cycle-con-esper-scepter |  | 0 | 0.0 | 0 | 3 |
| cycle-con-forward-synergy | cycle-con-forward-synergy |  | 0 | 0.0 | 0 | 4 |
| cycle-con-r-tricolor | cycle-con-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-con-shard-ability | cycle-con-shard-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-con-wubrg-ability | cycle-con-wubrg-ability |  | 0 | 0.0 | 0 | 3 |
| cycle-csp-allied-cumulative | cycle-csp-allied-cumulative |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-kindle-spell | cycle-csp-kindle-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-martyr | cycle-csp-martyr |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-pitchspell | cycle-csp-pitchspell |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-r-tricolor | cycle-csp-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-rimewind-vertical | cycle-csp-rimewind-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-csp-snow-tapland | cycle-csp-snow-tapland |  | 0 | 0.0 | 0 | 5 |
| cycle-csp-surging-spell | cycle-csp-surging-spell | cycle-surging-spell | 0 | 0.0 | 0 | 5 |
| cycle-csp-u-two-color | cycle-csp-u-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-charm | cycle-da1-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-commander-tax | cycle-da1-commander-tax |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-detective | cycle-da1-detective |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-mono-eminence | cycle-da1-mono-eminence |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-poison-tolerance | cycle-da1-poison-tolerance |  | 0 | 0.0 | 0 | 6 |
| cycle-da1-spell-commander | cycle-da1-spell-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-stage | cycle-da1-stage |  | 0 | 0.0 | 0 | 7 |
| cycle-da1-taught-by | cycle-da1-taught-by |  | 0 | 0.0 | 0 | 5 |
| cycle-da1-unclaimed | cycle-da1-unclaimed |  | 0 | 0.0 | 0 | 5 |
| cycle-demigod-aura | cycle-demigod-aura |  | 0 | 0.0 | 0 | 10 |
| cycle-dft-draft-signpost | cycle-dft-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-dft-gearhulk | cycle-dft-gearhulk |  | 0 | 0.0 | 0 | 5 |
| cycle-dft-nonvehicle-signpost | cycle-dft-nonvehicle-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-dft-raceway | cycle-dft-raceway |  | 0 | 0.0 | 0 | 3 |
| cycle-dft-roads | cycle-dft-roads |  | 0 | 0.0 | 0 | 5 |
| cycle-dft-surveyor | cycle-dft-surveyor |  | 0 | 0.0 | 0 | 5 |
| cycle-dft-team-captain | cycle-dft-team-captain |  | 0 | 0.0 | 0 | 10 |
| cycle-dft-team-vehicle | cycle-dft-team-vehicle |  | 0 | 0.0 | 0 | 10 |
| cycle-dft-tyrant | cycle-dft-tyrant | cycle-dft-vanilla | 0 | 0.0 | 0 | 5 |
| cycle-dft-verge | cycle-dft-verge |  | 0 | 0.0 | 0 | 5 |
| cycle-dgm-c-guild-ability | cycle-dgm-c-guild-ability |  | 0 | 0.0 | 0 | 10 |
| cycle-dgm-cluestones | cycle-dgm-cluestones |  | 0 | 0.0 | 0 | 10 |
| cycle-dgm-draft-signpost | cycle-dgm-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-dgm-gatekeeper | cycle-dgm-gatekeeper |  | 0 | 0.0 | 0 | 5 |
| cycle-dgm-m-two-color | cycle-dgm-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-dgm-maze-elemental | cycle-dgm-maze-elemental |  | 0 | 0.0 | 0 | 5 |
| cycle-dgm-maze-runner | cycle-dgm-maze-runner |  | 0 | 0.0 | 0 | 10 |
| cycle-dgm-r-fuse | cycle-dgm-r-fuse |  | 0 | 0.0 | 0 | 5 |
| cycle-dgm-u-fuse | cycle-dgm-u-fuse |  | 0 | 0.0 | 0 | 10 |
| cycle-dis-eidolon | cycle-dis-eidolon |  | 0 | 0.0 | 0 | 5 |
| cycle-dis-r-split | cycle-dis-r-split |  | 0 | 0.0 | 0 | 5 |
| cycle-dka-increasing-flashback | cycle-dka-increasing-flashback |  | 0 | 0.0 | 0 | 5 |
| cycle-dka-monster-lord | cycle-dka-monster-lord |  | 0 | 0.0 | 0 | 4 |
| cycle-dmr-r-two-color | cycle-dmr-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-dmr-tricolor-legend | cycle-dmr-tricolor-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-c-back-ally-kicker | cycle-dmu-c-back-ally-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-c-back-en-kicker | cycle-dmu-c-back-en-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-c-for-ally-kicker | cycle-dmu-c-for-ally-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-c-for-en-kicker | cycle-dmu-c-for-en-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-defiler | cycle-dmu-defiler |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-dual-land | cycle-dmu-dual-land |  | 0 | 0.0 | 0 | 10 |
| cycle-dmu-jumpstart | cycle-dmu-jumpstart |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-lord | cycle-dmu-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-mn-signpost | cycle-dmu-mn-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-dmu-r-m-saga | cycle-dmu-r-m-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-r-two-color-legend | cycle-dmu-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-dmu-tricolor-legend | cycle-dmu-tricolor-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-u-back-ally-kicker | cycle-dmu-u-back-ally-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-u-back-en-kicker | cycle-dmu-u-back-en-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-u-for-ally-kicker | cycle-dmu-u-for-ally-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-u-for-en-kicker | cycle-dmu-u-for-en-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-u-saga | cycle-dmu-u-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-dmu-wedge-kicker | cycle-dmu-wedge-kicker |  | 0 | 0.0 | 0 | 5 |
| cycle-dom-legendary-sorcery | cycle-dom-legendary-sorcery |  | 0 | 0.0 | 0 | 6 |
| cycle-dom-memorial | cycle-dom-memorial |  | 0 | 0.0 | 0 | 5 |
| cycle-drc-alt-commander | cycle-drc-alt-commander |  | 0 | 0.0 | 0 | 2 |
| cycle-drc-face-commander | cycle-drc-face-commander |  | 0 | 0.0 | 0 | 2 |
| cycle-dsc-alt-commander | cycle-dsc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-dsc-face-commander | cycle-dsc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-dsk-draft-signpost | cycle-dsk-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-dsk-glimmer | cycle-dsk-glimmer |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-landcycler | cycle-dsk-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-leyline | cycle-dsk-leyline |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-m-room | cycle-dsk-m-room |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-overlord | cycle-dsk-overlord |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-r-two-color | cycle-dsk-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-dsk-thirteenland | cycle-dsk-thirteenland |  | 0 | 0.0 | 0 | 10 |
| cycle-dsk-u-room | cycle-dsk-u-room |  | 0 | 0.0 | 0 | 5 |
| cycle-dsk-verge | cycle-dsk-verge |  | 0 | 0.0 | 0 | 5 |
| cycle-dst-affinity-golem | cycle-dst-affinity-golem |  | 0 | 0.0 | 0 | 5 |
| cycle-dst-echoing-spell | cycle-dst-echoing-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-dst-pulse | cycle-dst-pulse | cycle-pulse | 0 | 0.0 | 0 | 5 |
| cycle-dtk-behold-dragon | cycle-dtk-behold-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-command | cycle-dtk-command | cycle-tarkir-command | 0 | 0.0 | 0 | 5 |
| cycle-dtk-dragonlord | cycle-dtk-dragonlord |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-enemy-hate | cycle-dtk-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-monument | cycle-dtk-monument |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-r-megamorpher | cycle-dtk-r-megamorpher |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-r-two-color-dragon | cycle-dtk-r-two-color-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-regent | cycle-dtk-regent |  | 0 | 0.0 | 0 | 5 |
| cycle-dtk-u-monocolor-dragon | cycle-dtk-u-monocolor-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-dual-creatureland | cycle-dual-creatureland |  | 0 | 0.0 | 0 | 20 |
| cycle-dual-cycling-land | cycle-dual-cycling-land | cycle-bicycle-land | 0 | 0.0 | 0 | 10 |
| cycle-dual-investigate-tapland | cycle-dual-investigate-tapland |  | 0 | 0.0 | 0 | 10 |
| cycle-dual-surveil-land | cycle-dual-surveil-land | cycle-mkm-surveil-land | 0 | 0.0 | 0 | 10 |
| cycle-dual-tapland | cycle-dual-tapland |  | 0 | 0.0 | 0 | 10 |
| cycle-ecc-incarnation | cycle-ecc-incarnation |  | 0 | 0.0 | 0 | 5 |
| cycle-ecl-incarnation | cycle-ecl-incarnation |  | 0 | 0.0 | 0 | 5 |
| cycle-ecl-typal-convoke | cycle-ecl-typal-convoke |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-adamant-land | cycle-eld-adamant-land | cycle-eld-wilds-land | 0 | 0.0 | 0 | 5 |
| cycle-eld-brawler | cycle-eld-brawler |  | 0 | 0.0 | 0 | 4 |
| cycle-eld-c-adamant-spell | cycle-eld-c-adamant-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-castle | cycle-eld-castle |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-color-equipment | cycle-eld-color-equipment |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-color-hate | cycle-eld-color-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-court-artifact | cycle-eld-court-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-draft-signpost | cycle-eld-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-eld-hybrid | cycle-eld-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-eld-paladin | cycle-eld-paladin |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-r-adventurer | cycle-eld-r-adventurer |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-r-m-two-color | cycle-eld-r-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-eld-u-adamant-spell | cycle-eld-u-adamant-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-eld-u-two-color | cycle-eld-u-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-ema-r-two-color | cycle-ema-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-ema-tutor | cycle-ema-tutor |  | 0 | 0.0 | 0 | 5 |
| cycle-emn-allied-creature | cycle-emn-allied-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-emn-draft-signpost | cycle-emn-draft-signpost |  | 0 | 0.0 | 0 | 5 |
| cycle-emn-escalate-borrowed | cycle-emn-escalate-borrowed |  | 0 | 0.0 | 0 | 3 |
| cycle-emn-escalate-collective | cycle-emn-escalate-collective |  | 0 | 0.0 | 0 | 3 |
| cycle-eoe-draft-signpost | cycle-eoe-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-eoe-legend-after | cycle-eoe-legend-after |  | 0 | 0.0 | 0 | 6 |
| cycle-eoe-legend-before | cycle-eoe-legend-before |  | 0 | 0.0 | 0 | 6 |
| cycle-eoe-planet | cycle-eoe-planet |  | 0 | 0.0 | 0 | 5 |
| cycle-eoe-r-mono-spacecraft | cycle-eoe-r-mono-spacecraft |  | 0 | 0.0 | 0 | 5 |
| cycle-eoe-r-two-color | cycle-eoe-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-eoe-u-spacecraft | cycle-eoe-u-spacecraft |  | 0 | 0.0 | 0 | 10 |
| cycle-eve-avatar | cycle-eve-avatar |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-c-hybrid-1-drop | cycle-eve-c-hybrid-1-drop |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-c-retrace | cycle-eve-c-retrace |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-demigod-aura | cycle-eve-demigod-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-filterland | cycle-eve-filterland |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-hatchling | cycle-eve-hatchling |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-hedge-mage | cycle-eve-hedge-mage |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-hybrid-modal | cycle-eve-hybrid-modal |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-mimic | cycle-eve-mimic |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-monocolor-hybrid | cycle-eve-monocolor-hybrid |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-r-chroma | cycle-eve-r-chroma |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-skulkin | cycle-eve-skulkin | cycle-skulkin | 0 | 0.0 | 0 | 5 |
| cycle-eve-u-hybrid-3-drop | cycle-eve-u-hybrid-3-drop |  | 0 | 0.0 | 0 | 5 |
| cycle-eve-untapper | cycle-eve-untapper |  | 0 | 0.0 | 0 | 5 |
| cycle-exo-keeper | cycle-exo-keeper |  | 0 | 0.0 | 0 | 5 |
| cycle-exo-oath | cycle-exo-oath |  | 0 | 0.0 | 0 | 5 |
| cycle-extraplanar-praetor | cycle-extraplanar-praetor |  | 0 | 0.0 | 0 | 5 |
| cycle-fastland | cycle-fastland |  | 0 | 0.0 | 0 | 10 |
| cycle-fdn-planeswalker | cycle-fdn-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-fem-artifact-boon | cycle-fem-artifact-boon |  | 0 | 0.0 | 0 | 5 |
| cycle-fem-sacland | cycle-fem-sacland |  | 0 | 0.0 | 0 | 5 |
| cycle-fem-storage-land | cycle-fem-storage-land |  | 0 | 0.0 | 0 | 5 |
| cycle-fetchland | cycle-fetchland |  | 0 | 0.0 | 0 | 10 |
| cycle-fic-alt-commander | cycle-fic-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-fic-face-commander | cycle-fic-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-fin-adventure-land | cycle-fin-adventure-land |  | 0 | 0.0 | 0 | 5 |
| cycle-fin-crystal | cycle-fin-crystal |  | 0 | 0.0 | 0 | 5 |
| cycle-fin-draft-signpost | cycle-fin-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-fin-dual-town | cycle-fin-dual-town |  | 0 | 0.0 | 0 | 10 |
| cycle-fin-landcycler | cycle-fin-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-fin-r-two-color | cycle-fin-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-fin-sidequest | cycle-fin-sidequest |  | 0 | 0.0 | 0 | 5 |
| cycle-fin-u-summon | cycle-fin-u-summon |  | 0 | 0.0 | 0 | 5 |
| cycle-force-elemental | cycle-force-elemental |  | 0 | 0.0 | 0 | 5 |
| cycle-fra-annex | cycle-fra-annex |  | 0 | 0.0 | 0 | 5 |
| cycle-fra-elder-sphinx | cycle-fra-elder-sphinx |  | 0 | 0.0 | 0 | 5 |
| cycle-fra-lorwyn-five | cycle-fra-lorwyn-five |  | 0 | 0.0 | 0 | 10 |
| cycle-fra-way-of-the | cycle-fra-way-of-the |  | 0 | 0.0 | 0 | 10 |
| cycle-frf-c-monocolor-manifest | cycle-frf-c-monocolor-manifest |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-c-two-color | cycle-frf-c-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-clan-enhanced | cycle-frf-clan-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-dragonlord | cycle-frf-dragonlord |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-hybrid-ability | cycle-frf-hybrid-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-khan | cycle-frf-khan |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-manifest-form | cycle-frf-manifest-form |  | 0 | 0.0 | 0 | 3 |
| cycle-frf-modal-etb-creature | cycle-frf-modal-etb-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-modal-spell | cycle-frf-modal-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-runemark | cycle-frf-runemark |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-siege | cycle-frf-siege |  | 0 | 0.0 | 0 | 5 |
| cycle-frf-u-4mm-dragon | cycle-frf-u-4mm-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-augur | cycle-fut-augur |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-c-cycling | cycle-fut-c-cycling |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-dual-land | cycle-fut-dual-land |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-grandeur-legend | cycle-fut-grandeur-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-magus | cycle-fut-magus |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-noncreature-morph | cycle-fut-noncreature-morph |  | 0 | 0.0 | 0 | 3 |
| cycle-fut-pact | cycle-fut-pact |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-recurring-suspend | cycle-fut-recurring-suspend | cycle-recurring-suspend-spell | 0 | 0.0 | 0 | 5 |
| cycle-fut-sliver | cycle-fut-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-spellshaper | cycle-fut-spellshaper |  | 0 | 0.0 | 0 | 6 |
| cycle-fut-utilityland | cycle-fut-utilityland |  | 0 | 0.0 | 0 | 5 |
| cycle-fut-vanilla | cycle-fut-vanilla |  | 0 | 0.0 | 0 | 5 |
| cycle-gn2-mythic | cycle-gn2-mythic |  | 0 | 0.0 | 0 | 5 |
| cycle-gn3-mythic | cycle-gn3-mythic |  | 0 | 0.0 | 0 | 5 |
| cycle-gnt-mythic | cycle-gnt-mythic |  | 0 | 0.0 | 0 | 5 |
| cycle-gpt-leyline | cycle-gpt-leyline |  | 0 | 0.0 | 0 | 5 |
| cycle-gpt-magemark | cycle-gpt-magemark |  | 0 | 0.0 | 0 | 5 |
| cycle-gpt-nephilim | cycle-gpt-nephilim | cycle-nephilim | 0 | 0.0 | 0 | 5 |
| cycle-gpt-rusalka | cycle-gpt-rusalka | cycle-rusalka | 0 | 0.0 | 0 | 5 |
| cycle-grn-c-guild-ability | cycle-grn-c-guild-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-guild-champion | cycle-grn-guild-champion |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-guildmage | cycle-grn-guildmage |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-guildmaster | cycle-grn-guildmaster |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-hybrid-creature | cycle-grn-hybrid-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-locket | cycle-grn-locket |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-m-guild-spell | cycle-grn-m-guild-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-mmnn | cycle-grn-mmnn |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-precon-tutor | cycle-grn-precon-tutor |  | 0 | 0.0 | 0 | 2 |
| cycle-grn-r-monocolor-care | cycle-grn-r-monocolor-care |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-r-split | cycle-grn-r-split |  | 0 | 0.0 | 0 | 5 |
| cycle-grn-u-split | cycle-grn-u-split |  | 0 | 0.0 | 0 | 5 |
| cycle-gtc-denizen | cycle-gtc-denizen |  | 0 | 0.0 | 0 | 5 |
| cycle-gtc-land-aura | cycle-gtc-land-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-gtc-m-monocolor | cycle-gtc-m-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-gtc-primordial | cycle-gtc-primordial |  | 0 | 0.0 | 0 | 5 |
| cycle-gtc-x-spell | cycle-gtc-x-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-hbg-alora | cycle-hbg-alora |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-amber | cycle-hbg-amber |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-draft-signpost | cycle-hbg-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-hbg-gale | cycle-hbg-gale |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-gate | cycle-hbg-gate |  | 0 | 0.0 | 0 | 5 |
| cycle-hbg-gut | cycle-hbg-gut |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-imoen | cycle-hbg-imoen |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-jaheira | cycle-hbg-jaheira |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-karlach | cycle-hbg-karlach |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-klement | cycle-hbg-klement |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-lae'zel | cycle-hbg-lae'zel |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-legend | cycle-hbg-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-hbg-lukamina | cycle-hbg-lukamina |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-lulu | cycle-hbg-lulu |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-rasaad | cycle-hbg-rasaad |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-sarevok | cycle-hbg-sarevok |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-shadowheart | cycle-hbg-shadowheart |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-skanos | cycle-hbg-skanos |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-u-specialize | cycle-hbg-u-specialize |  | 0 | 0.0 | 0 | 10 |
| cycle-hbg-vhal | cycle-hbg-vhal |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-viconia | cycle-hbg-viconia |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-wilson | cycle-hbg-wilson |  | 0 | 0.0 | 0 | 6 |
| cycle-hbg-wyll | cycle-hbg-wyll |  | 0 | 0.0 | 0 | 6 |
| cycle-hml-triland | cycle-hml-triland |  | 0 | 0.0 | 0 | 5 |
| cycle-hob-bear-vertical | cycle-hob-bear-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-hob-c-adventurer | cycle-hob-c-adventurer |  | 0 | 0.0 | 0 | 5 |
| cycle-hob-c-hybrid | cycle-hob-c-hybrid |  | 0 | 0.0 | 0 | 5 |
| cycle-hob-company | cycle-hob-company |  | 0 | 0.0 | 0 | 5 |
| cycle-hob-draft-signpost | cycle-hob-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-hob-typal-dual | cycle-hob-typal-dual |  | 0 | 0.0 | 0 | 5 |
| cycle-hob-u-hybrid | cycle-hob-u-hybrid |  | 0 | 0.0 | 0 | 5 |
| cycle-horizon-land | cycle-horizon-land | cycle-canopy-land | 0 | 0.0 | 0 | 6 |
| cycle-hou-allied-aftermath | cycle-hou-allied-aftermath |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-defeat | cycle-hou-defeat |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-desert-cycling-land | cycle-hou-desert-cycling-land |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-desert-painland | cycle-hou-desert-painland | cycle-desert-painland | 0 | 0.0 | 0 | 5 |
| cycle-hou-deserts-matter | cycle-hou-deserts-matter |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-draft-signpost | cycle-hou-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-hou-enemy-aftermath | cycle-hou-enemy-aftermath |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-god | cycle-hou-god |  | 0 | 0.0 | 0 | 3 |
| cycle-hou-gods-last-act | cycle-hou-gods-last-act | cycle-hou-gods-last-action | 0 | 0.0 | 0 | 5 |
| cycle-hou-hour | cycle-hou-hour |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-modal-spell | cycle-hou-modal-spell |  | 0 | 0.0 | 0 | 3 |
| cycle-hou-power-eternalizer | cycle-hou-power-eternalizer |  | 0 | 0.0 | 0 | 5 |
| cycle-hou-torment | cycle-hou-torment |  | 0 | 0.0 | 0 | 3 |
| cycle-hybrid-filterland | cycle-hybrid-filterland |  | 0 | 0.0 | 0 | 10 |
| cycle-ice-depletion-land | cycle-ice-depletion-land |  | 0 | 0.0 | 0 | 5 |
| cycle-ice-painland | cycle-ice-painland |  | 0 | 0.0 | 0 | 5 |
| cycle-ice-r-two-color | cycle-ice-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-ice-scarab | cycle-ice-scarab | cycle-scarab | 0 | 0.0 | 0 | 5 |
| cycle-ice-talisman | cycle-ice-talisman |  | 0 | 0.0 | 0 | 5 |
| cycle-ice-two-color-enemy-hate | cycle-ice-two-color-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-apex | cycle-iko-apex |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-apex-spell | cycle-iko-apex-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-c-keyword-boost | cycle-iko-c-keyword-boost |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-c-mutate | cycle-iko-c-mutate |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-companion | cycle-iko-companion |  | 0 | 0.0 | 0 | 10 |
| cycle-iko-counter-cycler | cycle-iko-counter-cycler |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-crystal | cycle-iko-crystal |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-draft-signpost | cycle-iko-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-iko-keyword-bonder | cycle-iko-keyword-bonder | cycle-iko-mentor-hybrid;cycle-iko-keyword-hybrid | 0 | 0.0 | 0 | 5 |
| cycle-iko-keyword-mentor | cycle-iko-keyword-mentor | cycle-iko-mentor-uncommon | 0 | 0.0 | 0 | 5 |
| cycle-iko-keyword-monster | cycle-iko-keyword-monster | cycle-iko-mentor-rare | 0 | 0.0 | 0 | 5 |
| cycle-iko-legendary-human | cycle-iko-legendary-human |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-modal-creature | cycle-iko-modal-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-mutate-hybrid | cycle-iko-mutate-hybrid |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-mutate-x | cycle-iko-mutate-x | cycle-iko-x-mutant | 0 | 0.0 | 0 | 5 |
| cycle-iko-mythos | cycle-iko-mythos |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-r-mutate | cycle-iko-r-mutate |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-signpost-creature | cycle-iko-signpost-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-signpost-noncreature | cycle-iko-signpost-noncreature |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-triome | cycle-iko-triome | cycle-iko-tricycle-land | 0 | 0.0 | 0 | 5 |
| cycle-iko-u-mutate | cycle-iko-u-mutate |  | 0 | 0.0 | 0 | 4 |
| cycle-iko-ultimatum | cycle-iko-ultimatum |  | 0 | 0.0 | 0 | 5 |
| cycle-iko-wedge-enchantment | cycle-iko-wedge-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-ima-draft-signpost | cycle-ima-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-infinity-stone | cycle-infinity-stone | cycle-terminus-stone | 0 | 0.0 | 0 | 2 |
| cycle-innistrad-legend-angel | cycle-innistrad-legend-angel |  | 0 | 0.0 | 0 | 5 |
| cycle-inr-delver | cycle-inr-delver |  | 0 | 0.0 | 0 | 3 |
| cycle-inr-draft-signpost | cycle-inr-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-inv-allied-2-2 | cycle-inv-allied-2-2 |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-allied-t-ability | cycle-inv-allied-t-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-apprentice | cycle-inv-apprentice | cycle-apprentice | 0 | 0.0 | 0 | 5 |
| cycle-inv-backward-ability | cycle-inv-backward-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-c-nonc-kicker-spell | cycle-inv-c-nonc-kicker-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-cameo | cycle-inv-cameo |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-djinn | cycle-inv-djinn |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-domain-spell | cycle-inv-domain-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-dragon-attendant | cycle-inv-dragon-attendant |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-emissary | cycle-inv-emissary |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-flash-sorcery | cycle-inv-flash-sorcery |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-forward-ability | cycle-inv-forward-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-leech | cycle-inv-leech |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-master | cycle-inv-master |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-mutation | cycle-inv-mutation |  | 0 | 0.0 | 0 | 4 |
| cycle-inv-primeval-dragon | cycle-inv-primeval-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-sac-enchantment | cycle-inv-sac-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-sacland | cycle-inv-sacland |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-selfbounce-aura | cycle-inv-selfbounce-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-inv-weaver | cycle-inv-weaver |  | 0 | 0.0 | 0 | 5 |
| cycle-isd-allied-flashback | cycle-isd-allied-flashback |  | 0 | 0.0 | 0 | 5 |
| cycle-isd-allied-utilityland | cycle-isd-allied-utilityland |  | 0 | 0.0 | 0 | 5 |
| cycle-isd-checkland | cycle-isd-checkland |  | 0 | 0.0 | 0 | 5 |
| cycle-isd-r-flashback | cycle-isd-r-flashback |  | 0 | 0.0 | 0 | 5 |
| cycle-j21-perpetual | cycle-j21-perpetual |  | 0 | 0.0 | 0 | 5 |
| cycle-j21-planeswalker | cycle-j21-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-j22-hybrid-legend | cycle-j22-hybrid-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-j22-m-mono-legend | cycle-j22-m-mono-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-jmp-hybrid-legend | cycle-jmp-hybrid-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-jmp-thriving-land | cycle-jmp-thriving-land |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-c-heroic-grower | cycle-jou-c-heroic-grower |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-c-strive | cycle-jou-c-strive |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-draft-signpost | cycle-jou-draft-signpost |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-font | cycle-jou-font |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-land-type-matters | cycle-jou-land-type-matters |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-minor-god | cycle-jou-minor-god |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-nymph | cycle-jou-nymph |  | 0 | 0.0 | 0 | 5 |
| cycle-jou-u-bestow | cycle-jou-u-bestow |  | 0 | 0.0 | 0 | 5 |
| cycle-jud-1mv-martyr | cycle-jud-1mv-martyr | cycle-jud-1cmc-martyr | 0 | 0.0 | 0 | 5 |
| cycle-jud-gorger-vertical | cycle-jud-gorger-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-jud-incarnation | cycle-jud-incarnation |  | 0 | 0.0 | 0 | 5 |
| cycle-jud-wish | cycle-jud-wish |  | 0 | 0.0 | 0 | 5 |
| cycle-jud-wormfang-vertical | cycle-jud-wormfang-vertical |  | 0 | 0.0 | 0 | 6 |
| cycle-jumpstart-hybrid-legend | cycle-jumpstart-hybrid-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-keyrune | cycle-keyrune |  | 0 | 0.0 | 0 | 10 |
| cycle-khc-face-commander | cycle-khc-face-commander |  | 0 | 0.0 | 0 | 2 |
| cycle-khm-draft-signpost | cycle-khm-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-khm-legendary-signpost | cycle-khm-legendary-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-khm-living-weapon | cycle-khm-living-weapon |  | 0 | 0.0 | 0 | 5 |
| cycle-khm-m-foretell-spell | cycle-khm-m-foretell-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-khm-m-god | cycle-khm-m-god |  | 0 | 0.0 | 0 | 5 |
| cycle-khm-pathway | cycle-khm-pathway |  | 0 | 0.0 | 0 | 4 |
| cycle-khm-r-god | cycle-khm-r-god |  | 0 | 0.0 | 0 | 7 |
| cycle-khm-r-saga | cycle-khm-r-saga |  | 0 | 0.0 | 0 | 10 |
| cycle-khm-realm | cycle-khm-realm |  | 0 | 0.0 | 0 | 10 |
| cycle-khm-rune | cycle-khm-rune |  | 0 | 0.0 | 0 | 5 |
| cycle-khm-snow-scaler | cycle-khm-snow-scaler |  | 0 | 0.0 | 0 | 5 |
| cycle-khm-snow-tapland | cycle-khm-snow-tapland |  | 0 | 0.0 | 0 | 10 |
| cycle-khm-u-saga | cycle-khm-u-saga |  | 0 | 0.0 | 0 | 10 |
| cycle-kld-color-artifact | cycle-kld-color-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-kld-fastland | cycle-kld-fastland |  | 0 | 0.0 | 0 | 5 |
| cycle-kld-gearhulk | cycle-kld-gearhulk |  | 0 | 0.0 | 0 | 5 |
| cycle-kld-module | cycle-kld-module |  | 0 | 0.0 | 0 | 3 |
| cycle-kld-puzzleknot | cycle-kld-puzzleknot | cycle-puzzleknot | 0 | 0.0 | 0 | 5 |
| cycle-kld-thriving-creature | cycle-kld-thriving-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-ascendancy | cycle-ktk-ascendancy |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-banner | cycle-ktk-banner |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-c-3mno-creature | cycle-ktk-c-3mno-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-charm | cycle-ktk-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-draft-signpost | cycle-ktk-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-ktk-enemy-ability | cycle-ktk-enemy-ability |  | 0 | 0.0 | 0 | 10 |
| cycle-ktk-khan | cycle-ktk-khan |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-r-2mno-creature | cycle-ktk-r-2mno-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-r-two-color | cycle-ktk-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-reveal-morpher | cycle-ktk-reveal-morpher |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-u-2mno-creature | cycle-ktk-u-2mno-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-ktk-wedgeland | cycle-ktk-wedgeland |  | 0 | 0.0 | 0 | 5 |
| cycle-lcc-alt-commander | cycle-lcc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-lcc-face-commander | cycle-lcc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-lci-c-craft | cycle-lci-c-craft |  | 0 | 0.0 | 0 | 5 |
| cycle-lci-draft-signpost | cycle-lci-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-lci-god | cycle-lci-god |  | 0 | 0.0 | 0 | 5 |
| cycle-lci-hidden-land | cycle-lci-hidden-land |  | 0 | 0.0 | 0 | 5 |
| cycle-lci-landcycler | cycle-lci-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-lci-r-land-dfc | cycle-lci-r-land-dfc |  | 0 | 0.0 | 0 | 5 |
| cycle-lci-r-two-color | cycle-lci-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-lci-restless-land | cycle-lci-restless-land |  | 0 | 0.0 | 0 | 5 |
| cycle-lea-lace | cycle-lea-lace |  | 0 | 0.0 | 0 | 5 |
| cycle-lea-lucky-charm | cycle-lea-lucky-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-lea-moxen | cycle-lea-moxen |  | 0 | 0.0 | 0 | 5 |
| cycle-lea-red-escalate | cycle-lea-red-escalate |  | 0 | 0.0 | 0 | 3 |
| cycle-lea-slush-art | cycle-lea-slush-art | cycle-lea-top-down | 0 | 0.0 | 0 | 5 |
| cycle-lea-ward | cycle-lea-ward |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-anti-landwalk-enchant | cycle-leg-anti-landwalk-enchant |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-banding-land | cycle-leg-banding-land |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-battery | cycle-leg-battery |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-color-wash-instant | cycle-leg-color-wash-instant | cycle-color-wash-instant | 0 | 0.0 | 0 | 5 |
| cycle-leg-elder-dragon | cycle-leg-elder-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-glyph | cycle-leg-glyph |  | 0 | 0.0 | 0 | 5 |
| cycle-leg-legendary-land | cycle-leg-legendary-land |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-c-sliver | cycle-lgn-c-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-gempalm | cycle-lgn-gempalm |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-invoker | cycle-lgn-invoker |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-muse | cycle-lgn-muse |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-r-sliver | cycle-lgn-r-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-lgn-u-sliver | cycle-lgn-u-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-c-changeling | cycle-lrw-c-changeling |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-clash-counter-creature | cycle-lrw-clash-counter-creature | cycle-clash-counter-creature | 0 | 0.0 | 0 | 5 |
| cycle-lrw-harbinger | cycle-lrw-harbinger |  | 0 | 0.0 | 0 | 8 |
| cycle-lrw-hideaway-land | cycle-lrw-hideaway-land | cycle-hideaway-land | 0 | 0.0 | 0 | 5 |
| cycle-lrw-incarnation | cycle-lrw-incarnation |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-legend | cycle-lrw-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-r-champion | cycle-lrw-r-champion |  | 0 | 0.0 | 0 | 6 |
| cycle-lrw-r-changeling | cycle-lrw-r-changeling |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-token-fuel | cycle-lrw-token-fuel |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-typal-cantrip | cycle-lrw-typal-cantrip |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-typal-dual-land | cycle-lrw-typal-dual-land | cycle-lrw-tribal-dual-land | 0 | 0.0 | 0 | 5 |
| cycle-lrw-typal-legend | cycle-lrw-typal-legend |  | 0 | 0.0 | 0 | 8 |
| cycle-lrw-typal-revealer | cycle-lrw-typal-revealer |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-u-changeling | cycle-lrw-u-changeling |  | 0 | 0.0 | 0 | 5 |
| cycle-lrw-velis-vel | cycle-lrw-velis-vel |  | 0 | 0.0 | 0 | 3 |
| cycle-lrw-vivid-land | cycle-lrw-vivid-land |  | 0 | 0.0 | 0 | 5 |
| cycle-ltc-alt-commander | cycle-ltc-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-ltc-face-commander | cycle-ltc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-ltr-draft-signpost | cycle-ltr-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-ltr-landcycler | cycle-ltr-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-ltr-legendary-land | cycle-ltr-legendary-land |  | 0 | 0.0 | 0 | 5 |
| cycle-ltr-r-saga | cycle-ltr-r-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-ltr-r-two-color | cycle-ltr-r-two-color |  | 0 | 0.0 | 0 | 20 |
| cycle-ltr-u-saga | cycle-ltr-u-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-m10-checkland | cycle-m10-checkland |  | 0 | 0.0 | 0 | 5 |
| cycle-m11-leyline | cycle-m11-leyline |  | 0 | 0.0 | 0 | 5 |
| cycle-m11-typal-lord | cycle-m11-typal-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-legend | cycle-m13-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-legend-spell | cycle-m13-legend-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-planeswalker | cycle-m13-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-pw-hallmark | cycle-m13-pw-hallmark |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-pw-signature | cycle-m13-pw-signature |  | 0 | 0.0 | 0 | 5 |
| cycle-m13-sedge-creature | cycle-m13-sedge-creature | cycle-sedge-creature | 0 | 0.0 | 0 | 5 |
| cycle-m13-shandalar-ring | cycle-m13-shandalar-ring |  | 0 | 0.0 | 0 | 5 |
| cycle-m14-iconic-creature | cycle-m14-iconic-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-m14-magus-staff | cycle-m14-magus-staff |  | 0 | 0.0 | 0 | 5 |
| cycle-m14-planeswalker | cycle-m14-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m14-r-sliver | cycle-m14-r-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-legend | cycle-m15-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-paragon | cycle-m15-paragon |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-planeswalker | cycle-m15-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-same-color-enhancer | cycle-m15-same-color-enhancer |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-sedge-creature | cycle-m15-sedge-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-sliver | cycle-m15-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-m15-soul | cycle-m15-soul |  | 0 | 0.0 | 0 | 6 |
| cycle-m19-bolas-reign | cycle-m19-bolas-reign |  | 0 | 0.0 | 0 | 3 |
| cycle-m19-dig-spell | cycle-m19-dig-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-elder-dragon | cycle-m19-elder-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-planeswalker | cycle-m19-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-precon-c | cycle-m19-precon-c |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-precon-planeswalker | cycle-m19-precon-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-precon-pw-enhanced | cycle-m19-precon-pw-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-signature-spell | cycle-m19-signature-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-m19-typal-lord | cycle-m19-typal-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-cavalier | cycle-m20-cavalier |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-chandra | cycle-m20-chandra |  | 0 | 0.0 | 0 | 3 |
| cycle-m20-color-artifact | cycle-m20-color-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-doubles | cycle-m20-doubles |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-iconic-legend | cycle-m20-iconic-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-leyline | cycle-m20-leyline |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-planeswalker | cycle-m20-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-precon-common | cycle-m20-precon-common |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-precon-planeswalker | cycle-m20-precon-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-precon-tutor | cycle-m20-precon-tutor |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-protection-creature | cycle-m20-protection-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-same-name-enhanced | cycle-m20-same-name-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-m20-wedge-legend | cycle-m20-wedge-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-basri-vertical | cycle-m21-basri-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-m21-chandra-vertical | cycle-m21-chandra-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-m21-draft-signpost | cycle-m21-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-m21-liliana-vertical | cycle-m21-liliana-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-m21-mono-teferi-legend | cycle-m21-mono-teferi-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-planeswalker | cycle-m21-planeswalker |  | 0 | 0.0 | 0 | 6 |
| cycle-m21-precon-c | cycle-m21-precon-c |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-precon-planeswalker | cycle-m21-precon-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-precon-tutor | cycle-m21-precon-tutor |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-precon-u | cycle-m21-precon-u |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-r-typal | cycle-m21-r-typal |  | 0 | 0.0 | 0 | 5 |
| cycle-m21-sanctum | cycle-m21-sanctum | cycle-m21-shrine | 0 | 0.0 | 0 | 6 |
| cycle-m21-teferi-vertical | cycle-m21-teferi-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-m3c-alt-commander | cycle-m3c-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-m3c-face-commander | cycle-m3c-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-m3c-lhurgoyf | cycle-m3c-lhurgoyf |  | 0 | 0.0 | 0 | 3 |
| cycle-mb2-dual-land | cycle-mb2-dual-land |  | 0 | 0.0 | 0 | 5 |
| cycle-mbc-mono-planeswalker | cycle-mbc-mono-planeswalker |  | 0 | 0.0 | 0 | 5 |
| cycle-mh1-draft-signpost | cycle-mh1-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mh1-force | cycle-mh1-force |  | 0 | 0.0 | 0 | 5 |
| cycle-mh1-monocolor-legend | cycle-mh1-monocolor-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-mh1-r-two-color | cycle-mh1-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-mh1-talisman | cycle-mh1-talisman |  | 0 | 0.0 | 0 | 5 |
| cycle-mh1-u-sliver | cycle-mh1-u-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-mh2-basic-landcycler | cycle-mh2-basic-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-mh2-bridge | cycle-mh2-bridge |  | 0 | 0.0 | 0 | 10 |
| cycle-mh2-c-draft-signpost | cycle-mh2-c-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mh2-converge | cycle-mh2-converge |  | 0 | 0.0 | 0 | 5 |
| cycle-mh2-draft-signpost | cycle-mh2-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-mh2-incarnation | cycle-mh2-incarnation |  | 0 | 0.0 | 0 | 5 |
| cycle-mh2-no-mana-cost-suspend | cycle-mh2-no-mana-cost-suspend |  | 0 | 0.0 | 0 | 6 |
| cycle-mh2-r-two-color-new | cycle-mh2-r-two-color-new |  | 0 | 0.0 | 0 | 10 |
| cycle-mh2-u-draft-signpost | cycle-mh2-u-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-c-draft-signpost | cycle-mh3-c-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-draft-signpost | cycle-mh3-draft-signpost |  | 0 | 0.0 | 0 | 30 |
| cycle-mh3-energy-reservedlist | cycle-mh3-energy-reservedlist |  | 0 | 0.0 | 0 | 4 |
| cycle-mh3-flare | cycle-mh3-flare |  | 0 | 0.0 | 0 | 5 |
| cycle-mh3-flip-walker | cycle-mh3-flip-walker |  | 0 | 0.0 | 0 | 5 |
| cycle-mh3-landscape | cycle-mh3-landscape |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-mdfc-dual-land | cycle-mh3-mdfc-dual-land |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-mdfc-mono-land | cycle-mh3-mdfc-mono-land |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-r-m-two-color | cycle-mh3-r-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-mh3-r-mono-land | cycle-mh3-r-mono-land |  | 0 | 0.0 | 0 | 5 |
| cycle-mh3-saga | cycle-mh3-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-mh3-u-draft-signpost | cycle-mh3-u-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mic-curse | cycle-mic-curse |  | 0 | 0.0 | 0 | 5 |
| cycle-mic-visions | cycle-mic-visions |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-adversary | cycle-mid-adversary |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-alt-transform | cycle-mid-alt-transform |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-black-werewolf | cycle-mid-black-werewolf |  | 0 | 0.0 | 0 | 3 |
| cycle-mid-c-typal | cycle-mid-c-typal |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-draft-signpost | cycle-mid-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mid-r-flashback | cycle-mid-r-flashback |  | 0 | 0.0 | 0 | 10 |
| cycle-mid-r-mono-werewolf | cycle-mid-r-mono-werewolf |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-r-two-color-legend | cycle-mid-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-mid-slowland | cycle-mid-slowland |  | 0 | 0.0 | 0 | 5 |
| cycle-mid-u-flashback | cycle-mid-u-flashback |  | 0 | 0.0 | 0 | 10 |
| cycle-mir-charm | cycle-mir-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-diamond | cycle-mir-diamond |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-dragon | cycle-mir-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-enemy-backward-hate | cycle-mir-enemy-backward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-enemy-forward-hate | cycle-mir-enemy-forward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-enemy-fw-protection | cycle-mir-enemy-fw-protection |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-fetchland | cycle-mir-fetchland |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-guildmage | cycle-mir-guildmage |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-instantment | cycle-mir-instantment | cycle-instantment | 0 | 0.0 | 0 | 5 |
| cycle-mir-monocolor-enemy-hate | cycle-mir-monocolor-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-two-color-enemy-hate | cycle-mir-two-color-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mir-x-allied-spell | cycle-mir-x-allied-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-mkc-alt-commander | cycle-mkc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-mkc-face-commander | cycle-mkc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-mkm-draft-signpost | cycle-mkm-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-mkm-hybrid-disguise | cycle-mkm-hybrid-disguise |  | 0 | 0.0 | 0 | 10 |
| cycle-mkm-m-two-color | cycle-mkm-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-mkm-r-2c-noncreature | cycle-mkm-r-2c-noncreature |  | 0 | 0.0 | 0 | 10 |
| cycle-mkm-r-case | cycle-mkm-r-case |  | 0 | 0.0 | 0 | 5 |
| cycle-mkm-r-two-color-legend | cycle-mkm-r-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-mkm-split | cycle-mkm-split |  | 0 | 0.0 | 0 | 5 |
| cycle-mkm-u-gold-noncreature | cycle-mkm-u-gold-noncreature |  | 0 | 0.0 | 0 | 10 |
| cycle-mm3-r-two-color | cycle-mm3-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-mmq-c-spellshaper | cycle-mmq-c-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-cateran-recruiter | cycle-mmq-cateran-recruiter |  | 0 | 0.0 | 0 | 6 |
| cycle-mmq-depletion-land | cycle-mmq-depletion-land |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-enemy-hate | cycle-mmq-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-flailing-creature | cycle-mmq-flailing-creature |  | 0 | 0.0 | 0 | 3 |
| cycle-mmq-flash-aura | cycle-mmq-flash-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-legate | cycle-mmq-legate |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-monger | cycle-mmq-monger |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-pitchspell | cycle-mmq-pitchspell |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-r-spellshaper | cycle-mmq-r-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-ramos-artifact | cycle-mmq-ramos-artifact | cycle-ramos-artifact | 0 | 0.0 | 0 | 5 |
| cycle-mmq-ramosian-recruiter | cycle-mmq-ramosian-recruiter |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-rishadan-pirate | cycle-mmq-rishadan-pirate |  | 0 | 0.0 | 0 | 3 |
| cycle-mmq-storage-land | cycle-mmq-storage-land |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-u-spellshaper | cycle-mmq-u-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-mmq-unwilling-creature | cycle-mmq-unwilling-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-moc-alt-commander | cycle-moc-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-moc-face-commander | cycle-moc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-moc-path | cycle-moc-path |  | 0 | 0.0 | 0 | 5 |
| cycle-moc-talent | cycle-moc-talent |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-c-dfc | cycle-mom-c-dfc |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-c-landcycler | cycle-mom-c-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-corrupted-dfc-leg | cycle-mom-corrupted-dfc-leg |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-draft-signpost | cycle-mom-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-mom-enemy-backward-dfc | cycle-mom-enemy-backward-dfc |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-enemy-forward-dfc | cycle-mom-enemy-forward-dfc |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-enemy-hate | cycle-mom-enemy-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-invasion-signpost | cycle-mom-invasion-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-mom-praetor | cycle-mom-praetor |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-tricolor-team-up | cycle-mom-tricolor-team-up |  | 0 | 0.0 | 0 | 5 |
| cycle-mom-two-color-team-up | cycle-mom-two-color-team-up |  | 0 | 0.0 | 0 | 10 |
| cycle-mom-u-mono-invasion | cycle-mom-u-mono-invasion |  | 0 | 0.0 | 0 | 10 |
| cycle-monocolor-gatewatch-oath | cycle-monocolor-gatewatch-oath |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-0-0-elemental | cycle-mor-0-0-elemental |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-c-changeling | cycle-mor-c-changeling |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-c-kinship | cycle-mor-c-kinship |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-clashback-spell | cycle-mor-clashback-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-typal-counter-lord | cycle-mor-typal-counter-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-typal-equipment | cycle-mor-typal-equipment |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-typal-reward-spell | cycle-mor-typal-reward-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-u-evoke | cycle-mor-u-evoke |  | 0 | 0.0 | 0 | 5 |
| cycle-mor-u-kinship | cycle-mor-u-kinship |  | 0 | 0.0 | 0 | 5 |
| cycle-morphling | cycle-morphling |  | 0 | 0.0 | 0 | 5 |
| cycle-mrd-artifact-land | cycle-mrd-artifact-land |  | 0 | 0.0 | 0 | 6 |
| cycle-mrd-golem | cycle-mrd-golem |  | 0 | 0.0 | 0 | 5 |
| cycle-mrd-r-color-artifact | cycle-mrd-r-color-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-mrd-replica | cycle-mrd-replica |  | 0 | 0.0 | 0 | 5 |
| cycle-mrd-shard | cycle-mrd-shard | cycle-shard | 0 | 0.0 | 0 | 5 |
| cycle-mrd-slith | cycle-mrd-slith | cycle-slith | 0 | 0.0 | 0 | 6 |
| cycle-mrd-talisman | cycle-mrd-talisman |  | 0 | 0.0 | 0 | 5 |
| cycle-mrd-tower | cycle-mrd-tower |  | 0 | 0.0 | 0 | 5 |
| cycle-msc-f4-spell | cycle-msc-f4-spell |  | 0 | 0.0 | 0 | 4 |
| cycle-msc-face-commander | cycle-msc-face-commander |  | 0 | 0.0 | 0 | 7 |
| cycle-msc-fantastic-four | cycle-msc-fantastic-four |  | 0 | 0.0 | 0 | 4 |
| cycle-msc-landcycler | cycle-msc-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-msc-origin | cycle-msc-origin |  | 0 | 0.0 | 0 | 5 |
| cycle-msh-c-modal-teamwork | cycle-msh-c-modal-teamwork |  | 0 | 0.0 | 0 | 5 |
| cycle-msh-draft-signpost | cycle-msh-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-msh-fantastic-four | cycle-msh-fantastic-four |  | 0 | 0.0 | 0 | 4 |
| cycle-msh-gainland | cycle-msh-gainland |  | 0 | 0.0 | 0 | 10 |
| cycle-msh-hybrid | cycle-msh-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-msh-lair-dual | cycle-msh-lair-dual |  | 0 | 0.0 | 0 | 5 |
| cycle-msh-landcycler | cycle-msh-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-msh-u-plan | cycle-msh-u-plan |  | 0 | 0.0 | 0 | 5 |
| cycle-napland | cycle-napland |  | 0 | 0.0 | 0 | 10 |
| cycle-ncc-alt-commander | cycle-ncc-alt-commander | cycle-ncc-secondary-commander | 0 | 0.0 | 0 | 5 |
| cycle-ncc-confluence | cycle-ncc-confluence |  | 0 | 0.0 | 0 | 5 |
| cycle-ncc-enemy-multicolored | cycle-ncc-enemy-multicolored |  | 0 | 0.0 | 0 | 5 |
| cycle-ncc-face-commander | cycle-ncc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-ncc-r-two-color-legend | cycle-ncc-r-two-color-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-ncc-tri-legend-reprint | cycle-ncc-tri-legend-reprint |  | 0 | 0.0 | 0 | 5 |
| cycle-nec-myojin | cycle-nec-myojin |  | 0 | 0.0 | 0 | 5 |
| cycle-nem-c-spellshaper | cycle-nem-c-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-nem-fading-creature | cycle-nem-fading-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-nem-free-spell | cycle-nem-free-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-nem-parallax | cycle-nem-parallax |  | 0 | 0.0 | 0 | 3 |
| cycle-nem-recruiter | cycle-nem-recruiter |  | 0 | 0.0 | 0 | 3 |
| cycle-nem-seal | cycle-nem-seal | cycle-seal | 0 | 0.0 | 0 | 5 |
| cycle-neo-draft-signpost | cycle-neo-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-neo-dragon | cycle-neo-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-neo-invoke | cycle-neo-invoke |  | 0 | 0.0 | 0 | 5 |
| cycle-neo-legendary-land | cycle-neo-legendary-land |  | 0 | 0.0 | 0 | 5 |
| cycle-neo-march | cycle-neo-march |  | 0 | 0.0 | 0 | 5 |
| cycle-neo-shrine | cycle-neo-shrine |  | 0 | 0.0 | 0 | 6 |
| cycle-nonmana-land | cycle-nonmana-land |  | 0 | 0.0 | 0 | 25 |
| cycle-nph-chancellor | cycle-nph-chancellor |  | 0 | 0.0 | 0 | 5 |
| cycle-nph-exarch | cycle-nph-exarch |  | 0 | 0.0 | 0 | 5 |
| cycle-nph-praetor | cycle-nph-praetor |  | 0 | 0.0 | 0 | 5 |
| cycle-nph-shrine | cycle-nph-shrine | cycle-newphyrexia-shrine | 0 | 0.0 | 0 | 5 |
| cycle-nph-souleater | cycle-nph-souleater |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-allied-atog | cycle-ody-allied-atog |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-ally-filterland | cycle-ody-ally-filterland |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-burst | cycle-ody-burst |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-desire | cycle-ody-desire |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-egg | cycle-ody-egg |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-filterland | cycle-ody-filterland | cycle-signet-land | 0 | 0.0 | 0 | 10 |
| cycle-ody-hound | cycle-ody-hound |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-land-aura | cycle-ody-land-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-lhurgoyf | cycle-ody-lhurgoyf |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-mmm-lord | cycle-ody-mmm-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-r-two-color | cycle-ody-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-restock-creature | cycle-ody-restock-creature |  | 0 | 0.0 | 0 | 3 |
| cycle-ody-rites | cycle-ody-rites | cycle-rites | 0 | 0.0 | 0 | 5 |
| cycle-ody-sacland | cycle-ody-sacland |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-shrine | cycle-ody-shrine |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-sphere | cycle-ody-sphere |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-thought-beast | cycle-ody-thought-beast |  | 0 | 0.0 | 0 | 3 |
| cycle-ody-threshold-painland | cycle-ody-threshold-painland | cycle-threshold-painland | 0 | 0.0 | 0 | 5 |
| cycle-ody-wincon-enchantment | cycle-ody-wincon-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-ody-x-of-the-y | cycle-ody-x-of-the-y |  | 0 | 0.0 | 0 | 3 |
| cycle-ogw-draft-signpost | cycle-ogw-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-ogw-tapland | cycle-ogw-tapland |  | 0 | 0.0 | 0 | 5 |
| cycle-one-colored-sphere | cycle-one-colored-sphere |  | 0 | 0.0 | 0 | 5 |
| cycle-one-dominus | cycle-one-dominus |  | 0 | 0.0 | 0 | 5 |
| cycle-one-draft-signpost | cycle-one-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-one-skullbomb | cycle-one-skullbomb |  | 0 | 0.0 | 0 | 5 |
| cycle-one-sun-twilight | cycle-one-sun-twilight |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-aura-crown | cycle-ons-aura-crown |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-avatar | cycle-ons-avatar |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-c-cycle-effect | cycle-ons-c-cycle-effect |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-chain-spell | cycle-ons-chain-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-charm | cycle-ons-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-courier | cycle-ons-courier |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-cycling-matters | cycle-ons-cycling-matters |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-fetchland | cycle-ons-fetchland |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-symbiotic-vertical | cycle-ons-symbiotic-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-ons-typal-land | cycle-ons-typal-land |  | 0 | 0.0 | 0 | 8 |
| cycle-ons-u-cycle-effect | cycle-ons-u-cycle-effect |  | 0 | 0.0 | 0 | 5 |
| cycle-ons-word | cycle-ons-word |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-c-spell-mastery | cycle-ori-c-spell-mastery |  | 0 | 0.0 | 0 | 7 |
| cycle-ori-draft-signpost | cycle-ori-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-ori-flip-walker | cycle-ori-flip-walker |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-mentor | cycle-ori-mentor |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-plane-enchantment | cycle-ori-plane-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-r-spell-mastery | cycle-ori-r-spell-mastery |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-same-name-enhanced | cycle-ori-same-name-enhanced |  | 0 | 0.0 | 0 | 5 |
| cycle-ori-u-spell-mastery | cycle-ori-u-spell-mastery |  | 0 | 0.0 | 0 | 5 |
| cycle-otc-alt-commander | cycle-otc-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-otc-face-commander | cycle-otc-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-otj-draft-signpost | cycle-otj-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-otj-join-up | cycle-otj-join-up |  | 0 | 0.0 | 0 | 5 |
| cycle-otj-pingland | cycle-otj-pingland |  | 0 | 0.0 | 0 | 10 |
| cycle-otj-r-monocolor-mount | cycle-otj-r-monocolor-mount |  | 0 | 0.0 | 0 | 5 |
| cycle-otj-u-legend | cycle-otj-u-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-painland | cycle-painland |  | 0 | 0.0 | 0 | 10 |
| cycle-pathway | cycle-pathway |  | 0 | 0.0 | 0 | 10 |
| cycle-pc2-legend | cycle-pc2-legend |  | 0 | 0.0 | 0 | 4 |
| cycle-pcy-ability-losing-creature | cycle-pcy-ability-losing-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-pcy-field-aura | cycle-pcy-field-aura | cycle-field-aura | 0 | 0.0 | 0 | 5 |
| cycle-pcy-legendary-spellshaper | cycle-pcy-legendary-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-pcy-rhystic-bonus | cycle-pcy-rhystic-bonus |  | 0 | 0.0 | 0 | 5 |
| cycle-pcy-spellshaper-aura | cycle-pcy-spellshaper-aura | cycle-spellshaper-aura | 0 | 0.0 | 0 | 5 |
| cycle-pcy-wind | cycle-pcy-wind |  | 0 | 0.0 | 0 | 5 |
| cycle-pip-alt-commander | cycle-pip-alt-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-pip-enemy-filterland | cycle-pip-enemy-filterland | cycle-pip-filterland | 0 | 0.0 | 0 | 5 |
| cycle-pip-face-commander | cycle-pip-face-commander |  | 0 | 0.0 | 0 | 4 |
| cycle-playtest-dual-land | cycle-playtest-dual-land |  | 0 | 0.0 | 0 | 10 |
| cycle-plc-c-sliver | cycle-plc-c-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-charm | cycle-plc-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-enemy-sliver | cycle-plc-enemy-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-extortion-vertical | cycle-plc-extortion-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-plc-magus | cycle-plc-magus |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-primeval-dragon | cycle-plc-primeval-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-spellshaper | cycle-plc-spellshaper |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-split-vertical | cycle-plc-split-vertical |  | 0 | 0.0 | 0 | 3 |
| cycle-plc-suspend-x-creature | cycle-plc-suspend-x-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-plc-u-vanishing-creature | cycle-plc-u-vanishing-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-battlemage | cycle-pls-battlemage |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-c-gating-creature | cycle-pls-c-gating-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-c-two-color | cycle-pls-c-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-cantrip | cycle-pls-cantrip |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-lair | cycle-pls-lair |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-primeval-charm | cycle-pls-primeval-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-pw-enchantment | cycle-pls-pw-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-r-tricolor | cycle-pls-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-pls-r-two-color | cycle-pls-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-pls-sacland-kicker-spell | cycle-pls-sacland-kicker-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-primeval-dragon | cycle-primeval-dragon |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-backward-ability | cycle-rav-backward-ability |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-etb-aura | cycle-rav-etb-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-rav-forward-ability | cycle-rav-forward-ability |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-guild-artifact | cycle-rav-guild-artifact |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-guildhall | cycle-rav-guildhall |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-guildmaster | cycle-rav-guildmaster |  | 0 | 0.0 | 0 | 10 |
| cycle-rav-hunted-creature | cycle-rav-hunted-creature | cycle-hunted-creature | 0 | 0.0 | 0 | 5 |
| cycle-rav-mmn | cycle-rav-mmn |  | 0 | 0.0 | 0 | 11 |
| cycle-rav-shockland | cycle-rav-shockland | cycle-shockland | 0 | 0.0 | 0 | 10 |
| cycle-restless-land | cycle-restless-land |  | 0 | 0.0 | 0 | 10 |
| cycle-restock-legendary-land | cycle-restock-legendary-land |  | 0 | 0.0 | 0 | 3 |
| cycle-reveal-land | cycle-reveal-land |  | 0 | 0.0 | 0 | 10 |
| cycle-rix-c-typal-boost | cycle-rix-c-typal-boost |  | 0 | 0.0 | 0 | 10 |
| cycle-rix-draft-signpost | cycle-rix-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-rix-forerunner | cycle-rix-forerunner |  | 0 | 0.0 | 0 | 4 |
| cycle-rix-immortal-sun-purpose | cycle-rix-immortal-sun-purpose |  | 0 | 0.0 | 0 | 4 |
| cycle-rix-legendary-transform | cycle-rix-legendary-transform |  | 0 | 0.0 | 0 | 5 |
| cycle-rix-m-monocolor | cycle-rix-m-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-rix-typal-revealer | cycle-rix-typal-revealer |  | 0 | 0.0 | 0 | 4 |
| cycle-rna-c-guild-ability | cycle-rna-c-guild-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-guild-champion | cycle-rna-guild-champion |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-guild-color-ability | cycle-rna-guild-color-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-guildmage | cycle-rna-guildmage |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-guildmaster | cycle-rna-guildmaster |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-hybrid-creature | cycle-rna-hybrid-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-locket | cycle-rna-locket |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-m-guild-spell | cycle-rna-m-guild-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-m-monocolor | cycle-rna-m-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-mmnn | cycle-rna-mmnn |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-r-split | cycle-rna-r-split |  | 0 | 0.0 | 0 | 5 |
| cycle-rna-u-split | cycle-rna-u-split |  | 0 | 0.0 | 0 | 5 |
| cycle-roe-invoker | cycle-roe-invoker |  | 0 | 0.0 | 0 | 5 |
| cycle-roe-titan | cycle-roe-titan |  | 0 | 0.0 | 0 | 3 |
| cycle-rtr-land-aura | cycle-rtr-land-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-rtr-m-monocolor | cycle-rtr-m-monocolor |  | 0 | 0.0 | 0 | 5 |
| cycle-rtr-m-two-color | cycle-rtr-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-rtr-uncounterable-spell | cycle-rtr-uncounterable-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-rvr-r-guild-spell | cycle-rvr-r-guild-spell |  | 0 | 0.0 | 0 | 10 |
| cycle-rvr-r-mono-legend | cycle-rvr-r-mono-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-s99-vanilla-1-drop | cycle-s99-vanilla-1-drop |  | 0 | 0.0 | 0 | 5 |
| cycle-scd-face-commander | cycle-scd-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-scg-c-storm-instant | cycle-scg-c-storm-instant |  | 0 | 0.0 | 0 | 5 |
| cycle-scg-decree | cycle-scg-decree |  | 0 | 0.0 | 0 | 5 |
| cycle-scg-dragon-aura | cycle-scg-dragon-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-scg-mv-matters | cycle-scg-mv-matters | cycle-scg-cmc-matters | 0 | 0.0 | 0 | 6 |
| cycle-scg-warchief | cycle-scg-warchief | cycle-warchief | 0 | 0.0 | 0 | 5 |
| cycle-shm-allied-conspire | cycle-shm-allied-conspire |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-allied-scarecrow | cycle-shm-allied-scarecrow |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-allied-selfboost | cycle-shm-allied-selfboost |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-avatar | cycle-shm-avatar |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-c-hybrid-1-drop | cycle-shm-c-hybrid-1-drop |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-cohort | cycle-shm-cohort |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-demigod-aura | cycle-shm-demigod-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-duo | cycle-shm-duo |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-filterland | cycle-shm-filterland |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-hate-enhanced-spell | cycle-shm-hate-enhanced-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-hideaway-creature | cycle-shm-hideaway-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-initiate | cycle-shm-initiate |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-mentor | cycle-shm-mentor |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-monocolored-conspire | cycle-shm-monocolored-conspire |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-permanent-count | cycle-shm-permanent-count |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-r-persist | cycle-shm-r-persist |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-reflection | cycle-shm-reflection |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-twobrid-spell | cycle-shm-twobrid-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-u-hybrid-3-drop | cycle-shm-u-hybrid-3-drop |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-unblockable-enemy | cycle-shm-unblockable-enemy |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-untap | cycle-shm-untap |  | 0 | 0.0 | 0 | 3 |
| cycle-shm-wisps | cycle-shm-wisps |  | 0 | 0.0 | 0 | 5 |
| cycle-shm-witch | cycle-shm-witch |  | 0 | 0.0 | 0 | 5 |
| cycle-shrine | cycle-shrine |  | 0 | 0.0 | 0 | 22 |
| cycle-slowland | cycle-slowland | slowland | 0 | 0.0 | 0 | 10 |
| cycle-snc-ascendancy | cycle-snc-ascendancy |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-c-signpost | cycle-snc-c-signpost |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-c-tapland | cycle-snc-c-tapland |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-charm | cycle-snc-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-color-hate | cycle-snc-color-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-draft-signpost | cycle-snc-draft-signpost |  | 0 | 0.0 | 0 | 15 |
| cycle-snc-fetchland | cycle-snc-fetchland |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-fixer | cycle-snc-fixer |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-hideaway | cycle-snc-hideaway |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-hybrid-legend | cycle-snc-hybrid-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-initiate | cycle-snc-initiate |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-leader | cycle-snc-leader |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-r-shard-removal | cycle-snc-r-shard-removal |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-r-tricolor | cycle-snc-r-tricolor |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-r-two-color | cycle-snc-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-triland | cycle-snc-triland |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-u-legend | cycle-snc-u-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-u-mno-henchman | cycle-snc-u-mno-henchman |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-u-signpost-creature | cycle-snc-u-signpost-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-snc-u-signpost-nonc | cycle-snc-u-signpost-nonc |  | 0 | 0.0 | 0 | 5 |
| cycle-soc-alt-commander | cycle-soc-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-soc-face-commander | cycle-soc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-soc-guest-lecturer | cycle-soc-guest-lecturer |  | 0 | 0.0 | 0 | 5 |
| cycle-soc-octoland | cycle-soc-octoland | cycle-soc-lateland;cycle-soc-turbulent-land | 0 | 0.0 | 0 | 5 |
| cycle-soc-two-color-prepare | cycle-soc-two-color-prepare |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-c-typal-boost | cycle-soi-c-typal-boost |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-crazed-creature | cycle-soi-crazed-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-draft-signpost | cycle-soi-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-soi-r-tdfc | cycle-soi-r-tdfc | cycle-soi-r-ndfc | 0 | 0.0 | 0 | 5 |
| cycle-soi-r-two-color | cycle-soi-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-reveal-land | cycle-soi-reveal-land |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-tapland | cycle-soi-tapland |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-typal-lord | cycle-soi-typal-lord |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-vessel | cycle-soi-vessel |  | 0 | 0.0 | 0 | 5 |
| cycle-soi-x-madness-sorcery | cycle-soi-x-madness-sorcery |  | 0 | 0.0 | 0 | 3 |
| cycle-sok-epic-sorcery | cycle-sok-epic-sorcery |  | 0 | 0.0 | 0 | 5 |
| cycle-sok-flip-ascendant | cycle-sok-flip-ascendant | cycle-flip-ascendant | 0 | 0.0 | 0 | 5 |
| cycle-sok-ghostlit-kami | cycle-sok-ghostlit-kami |  | 0 | 0.0 | 0 | 5 |
| cycle-sok-legendary-kirin | cycle-sok-legendary-kirin |  | 0 | 0.0 | 0 | 5 |
| cycle-sok-maro-creature | cycle-sok-maro-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-sok-onna | cycle-sok-onna |  | 0 | 0.0 | 0 | 5 |
| cycle-sok-upkeep-rescue | cycle-sok-upkeep-rescue |  | 0 | 0.0 | 0 | 5 |
| cycle-som-fastland | cycle-som-fastland |  | 0 | 0.0 | 0 | 5 |
| cycle-sorcery-magus | cycle-sorcery-magus |  | 0 | 0.0 | 0 | 5 |
| cycle-sos-dragon | cycle-sos-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-sos-emeritus | cycle-sos-emeritus |  | 0 | 0.0 | 0 | 5 |
| cycle-sos-lesson | cycle-sos-lesson | cycle-sos-paradigm | 0 | 0.0 | 0 | 5 |
| cycle-sos-r-2c-legend | cycle-sos-r-2c-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-spe-c-creature | cycle-spe-c-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-spe-face-legend | cycle-spe-face-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-spe-u-legend | cycle-spe-u-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-spirit-avatar | cycle-spirit-avatar |  | 0 | 0.0 | 0 | 10 |
| cycle-spm-saga | cycle-spm-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-spm-tmdfc | cycle-spm-tmdfc |  | 0 | 0.0 | 0 | 5 |
| cycle-sth-allied-sliver | cycle-sth-allied-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-sth-licid | cycle-sth-licid |  | 0 | 0.0 | 0 | 5 |
| cycle-sth-wall | cycle-sth-wall |  | 0 | 0.0 | 0 | 5 |
| cycle-stormscape-vertical | cycle-stormscape-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-stx-apprentice | cycle-stx-apprentice |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-a{a/b}b | cycle-stx-a{a/b}b |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-c-2c-creature | cycle-stx-c-2c-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-c-2c-noncreature | cycle-stx-c-2c-noncreature |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-campus | cycle-stx-campus |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-command | cycle-stx-command |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-dean | cycle-stx-dean |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-double-keyword | cycle-stx-double-keyword |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-draft-signpost | cycle-stx-draft-signpost |  | 0 | 0.0 | 0 | 15 |
| cycle-stx-dragon-founder | cycle-stx-dragon-founder |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-hhhh | cycle-stx-hhhh |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-m-college-spell | cycle-stx-m-college-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-m-mdfc | cycle-stx-m-mdfc |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-mastery | cycle-stx-mastery |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-pledgemage | cycle-stx-pledgemage |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-r-learner | cycle-stx-r-learner |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-r-lesson | cycle-stx-r-lesson |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-r-mdfc | cycle-stx-r-mdfc |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-reveal-land | cycle-stx-reveal-land |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-student | cycle-stx-student |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-summoning | cycle-stx-summoning |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-treasure-spell | cycle-stx-treasure-spell |  | 0 | 0.0 | 0 | 3 |
| cycle-stx-u-lesson | cycle-stx-u-lesson |  | 0 | 0.0 | 0 | 5 |
| cycle-stx-u-mono-magecraft | cycle-stx-u-mono-magecraft |  | 0 | 0.0 | 0 | 5 |
| cycle-sunscape-vertical | cycle-sunscape-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-sword-ally-color | cycle-sword-ally-color |  | 0 | 0.0 | 0 | 5 |
| cycle-sword-enemy-color | cycle-sword-enemy-color |  | 0 | 0.0 | 0 | 5 |
| cycle-talisman | cycle-talisman |  | 0 | 0.0 | 0 | 10 |
| cycle-tangoland | cycle-tangoland | cycle-tango-land | 0 | 0.0 | 0 | 10 |
| cycle-tbng-inspired-token | cycle-tbng-inspired-token |  | 0 | 0.0 | 0 | 5 |
| cycle-tdc-alt-commander | cycle-tdc-alt-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-tdc-face-commander | cycle-tdc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-tdc-will | cycle-tdc-will |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-c-behold | cycle-tdm-c-behold |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-c-omen | cycle-tdm-c-omen |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-c-twobrid | cycle-tdm-c-twobrid |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-devotee | cycle-tdm-devotee |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-draft-signpost | cycle-tdm-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-tdm-dragonstorm | cycle-tdm-dragonstorm |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-khan | cycle-tdm-khan |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-m-clan-spell | cycle-tdm-m-clan-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-monument | cycle-tdm-monument |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-r-dragon | cycle-tdm-r-dragon | cycle-tdm-regent | 0 | 0.0 | 0 | 5 |
| cycle-tdm-r-tricolor | cycle-tdm-r-tricolor |  | 0 | 0.0 | 0 | 10 |
| cycle-tdm-saga | cycle-tdm-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-siege | cycle-tdm-siege |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-spirit-dragon | cycle-tdm-spirit-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-u-omen | cycle-tdm-u-omen |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-u-twobrid | cycle-tdm-u-twobrid |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-u-wedge-dragon | cycle-tdm-u-wedge-dragon |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-u-wedge-nondragon | cycle-tdm-u-wedge-nondragon |  | 0 | 0.0 | 0 | 5 |
| cycle-tdm-utility-land | cycle-tdm-utility-land |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-c-removal-aura | cycle-thb-c-removal-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-demigod | cycle-thb-demigod |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-draft-signpost | cycle-thb-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-thb-intervention | cycle-thb-intervention |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-monocolor-god | cycle-thb-monocolor-god |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-nymph | cycle-thb-nymph |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-nyxborn | cycle-thb-nyxborn |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-omen | cycle-thb-omen |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-r-m-saga | cycle-thb-r-m-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-thb-r-m-two-color | cycle-thb-r-m-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-thb-u-saga | cycle-thb-u-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-thornscape-vertical | cycle-thornscape-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-ths-c-allied-ability | cycle-ths-c-allied-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-c-enemy-ability | cycle-ths-c-enemy-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-cantrip-aura | cycle-ths-cantrip-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-double-tactics | cycle-ths-double-tactics |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-draft-signpost | cycle-ths-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-ths-emissary | cycle-ths-emissary |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-god-weapon | cycle-ths-god-weapon |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-major-god | cycle-ths-major-god |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-nymph | cycle-ths-nymph |  | 0 | 0.0 | 0 | 5 |
| cycle-ths-r-two-color | cycle-ths-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-ths-self-hate | cycle-ths-self-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-thunderscape-vertical | cycle-thunderscape-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-tkhm-realm-token | cycle-tkhm-realm-token |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-ascension | cycle-tla-ascension |  | 0 | 0.0 | 0 | 4 |
| cycle-tla-basic-count | cycle-tla-basic-count |  | 0 | 0.0 | 0 | 5 |
| cycle-tla-bending-lesson | cycle-tla-bending-lesson |  | 0 | 0.0 | 0 | 4 |
| cycle-tla-c-hybrid | cycle-tla-c-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-c-tapland | cycle-tla-c-tapland |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-draft-signpost | cycle-tla-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-tla-landcycler | cycle-tla-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-tla-m-saga | cycle-tla-m-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-tla-r-two-color | cycle-tla-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-shrine | cycle-tla-shrine |  | 0 | 0.0 | 0 | 5 |
| cycle-tla-u-hybrid | cycle-tla-u-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-u-two-color | cycle-tla-u-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-tla-utility-land | cycle-tla-utility-land |  | 0 | 0.0 | 0 | 5 |
| cycle-tla-vertical-aang | cycle-tla-vertical-aang |  | 0 | 0.0 | 0 | 4 |
| cycle-tle-bending-master | cycle-tle-bending-master | cycle-tle-experience | 0 | 0.0 | 0 | 5 |
| cycle-tlrw-typal-token | cycle-tlrw-typal-token |  | 0 | 0.0 | 0 | 8 |
| cycle-tmc-character-select | cycle-tmc-character-select |  | 0 | 0.0 | 0 | 5 |
| cycle-tmc-face-commander | cycle-tmc-face-commander |  | 0 | 0.0 | 0 | 5 |
| cycle-tmc-m-turtle | cycle-tmc-m-turtle |  | 0 | 0.0 | 0 | 4 |
| cycle-tmc-teamup | cycle-tmc-teamup |  | 0 | 0.0 | 0 | 4 |
| cycle-tmp-c-sliver | cycle-tmp-c-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-enemy-backward-hate | cycle-tmp-enemy-backward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-enemy-forward-hate | cycle-tmp-enemy-forward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-licid | cycle-tmp-licid |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-medallion | cycle-tmp-medallion |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-napland | cycle-tmp-napland |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-pain-tapland | cycle-tmp-pain-tapland |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-r-two-color | cycle-tmp-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-u-sliver | cycle-tmp-u-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-tmp-u-two-color | cycle-tmp-u-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-avatar-vertical | cycle-tmt-avatar-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-tmt-c-hybrid | cycle-tmt-c-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-tmt-class | cycle-tmt-class |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-donatello-vertical | cycle-tmt-donatello-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-tmt-draft-signpost | cycle-tmt-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-tmt-enemy-ability | cycle-tmt-enemy-ability |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-gainland | cycle-tmt-gainland |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-landcycler | cycle-tmt-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-leonardo-vertical | cycle-tmt-leonardo-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-tmt-michelangelo-vert | cycle-tmt-michelangelo-vert |  | 0 | 0.0 | 0 | 4 |
| cycle-tmt-r-hybrid | cycle-tmt-r-hybrid |  | 0 | 0.0 | 0 | 10 |
| cycle-tmt-r-technique | cycle-tmt-r-technique |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-raphael-vertical | cycle-tmt-raphael-vertical |  | 0 | 0.0 | 0 | 4 |
| cycle-tmt-signpost-legend | cycle-tmt-signpost-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-signpost-noncreature | cycle-tmt-signpost-noncreature |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-team-up | cycle-tmt-team-up |  | 0 | 0.0 | 0 | 10 |
| cycle-tmt-u-equipment | cycle-tmt-u-equipment |  | 0 | 0.0 | 0 | 5 |
| cycle-tmt-u-technique | cycle-tmt-u-technique |  | 0 | 0.0 | 0 | 5 |
| cycle-tor-black-dreams | cycle-tor-black-dreams |  | 0 | 0.0 | 0 | 3 |
| cycle-tor-c-madness | cycle-tor-c-madness |  | 0 | 0.0 | 0 | 5 |
| cycle-tor-disorder-enchantment | cycle-tor-disorder-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-tor-possessed-creature | cycle-tor-possessed-creature |  | 0 | 0.0 | 0 | 4 |
| cycle-tor-r-dreams | cycle-tor-r-dreams |  | 0 | 0.0 | 0 | 5 |
| cycle-tor-red-punisher | cycle-tor-red-punisher |  | 0 | 0.0 | 0 | 3 |
| cycle-tor-tainted-land | cycle-tor-tainted-land |  | 0 | 0.0 | 0 | 4 |
| cycle-tor-threshold-etb | cycle-tor-threshold-etb |  | 0 | 0.0 | 0 | 5 |
| cycle-tor-u-madness | cycle-tor-u-madness |  | 0 | 0.0 | 0 | 5 |
| cycle-triple-one-drop | cycle-triple-one-drop |  | 0 | 0.0 | 0 | 3 |
| cycle-trk-anomaly | cycle-trk-anomaly |  | 0 | 0.0 | 0 | 5 |
| cycle-trk-draft-signpost | cycle-trk-draft-signpost |  | 0 | 0.0 | 0 | 20 |
| cycle-trk-hybrid-signpost | cycle-trk-hybrid-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-trk-landcycler | cycle-trk-landcycler |  | 0 | 0.0 | 0 | 5 |
| cycle-trk-mission | cycle-trk-mission |  | 0 | 0.0 | 0 | 5 |
| cycle-trk-modal-land | cycle-trk-modal-land |  | 0 | 0.0 | 0 | 5 |
| cycle-trk-planet | cycle-trk-planet |  | 0 | 0.0 | 0 | 10 |
| cycle-trk-test | cycle-trk-test |  | 0 | 0.0 | 0 | 5 |
| cycle-trk-u-saga | cycle-trk-u-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-addendum | cycle-tsp-addendum |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-allied-sliver | cycle-tsp-allied-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-c-sliver | cycle-tsp-c-sliver |  | 0 | 0.0 | 0 | 10 |
| cycle-tsp-flash-aura | cycle-tsp-flash-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-m-suspend-creature | cycle-tsp-m-suspend-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-magus | cycle-tsp-magus |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-no-mana-cost-suspend | cycle-tsp-no-mana-cost-suspend |  | 0 | 0.0 | 0 | 6 |
| cycle-tsp-perpetual-aura | cycle-tsp-perpetual-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-r-buyback | cycle-tsp-r-buyback |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-r-morph-creature | cycle-tsp-r-morph-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-r-sliver | cycle-tsp-r-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-r-split-second | cycle-tsp-r-split-second |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-storage-land | cycle-tsp-storage-land |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-time-removal | cycle-tsp-time-removal |  | 0 | 0.0 | 0 | 3 |
| cycle-tsp-totem | cycle-tsp-totem |  | 0 | 0.0 | 0 | 5 |
| cycle-tsp-u-sliver | cycle-tsp-u-sliver |  | 0 | 0.0 | 0 | 5 |
| cycle-tstx-mascot | cycle-tstx-mascot |  | 0 | 0.0 | 0 | 5 |
| cycle-turbulent-land | cycle-turbulent-land |  | 0 | 0.0 | 0 | 8 |
| cycle-uds-growing-enchantment | cycle-uds-growing-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-uds-lobotomy-spell | cycle-uds-lobotomy-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-uds-scent | cycle-uds-scent | cycle-scent | 0 | 0.0 | 0 | 5 |
| cycle-uds-seer | cycle-uds-seer | cycle-seer | 0 | 0.0 | 0 | 5 |
| cycle-ugl-double-spell | cycle-ugl-double-spell |  | 0 | 0.0 | 0 | 5 |
| cycle-ugl-multiplayer | cycle-ugl-multiplayer |  | 0 | 0.0 | 0 | 5 |
| cycle-ugl-rock-paper-scissors | cycle-ugl-rock-paper-scissors |  | 0 | 0.0 | 0 | 3 |
| cycle-ulg-creatureland | cycle-ulg-creatureland | cycle-usg-manland | 0 | 0.0 | 0 | 5 |
| cycle-ulg-perpetual-aura | cycle-ulg-perpetual-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-ulg-sleeping-enchantment | cycle-ulg-sleeping-enchantment |  | 0 | 0.0 | 0 | 5 |
| cycle-ulg-vertical-phyrexian | cycle-ulg-vertical-phyrexian |  | 0 | 0.0 | 0 | 4 |
| cycle-un-psychographics | cycle-un-psychographics |  | 0 | 0.0 | 0 | 4 |
| cycle-und-enemy-colored-legend | cycle-und-enemy-colored-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-c-blank | cycle-unf-c-blank |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-c-employee | cycle-unf-c-employee |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-draft-signpost | cycle-unf-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-unf-etb-attraction | cycle-unf-etb-attraction |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-i-spy | cycle-unf-i-spy |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-myra's-marvels | cycle-unf-myra's-marvels |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-single-sticker | cycle-unf-single-sticker |  | 0 | 0.0 | 0 | 6 |
| cycle-unf-sticker-activation | cycle-unf-sticker-activation |  | 0 | 0.0 | 0 | 5 |
| cycle-unf-stickered | cycle-unf-stickered |  | 0 | 0.0 | 0 | 3 |
| cycle-unf-u-blank | cycle-unf-u-blank |  | 0 | 0.0 | 0 | 5 |
| cycle-unh-c-gotcha | cycle-unh-c-gotcha |  | 0 | 0.0 | 0 | 5 |
| cycle-unh-donkey | cycle-unh-donkey |  | 0 | 0.0 | 0 | 5 |
| cycle-unh-minigame | cycle-unh-minigame |  | 0 | 0.0 | 0 | 5 |
| cycle-unh-u-gotcha | cycle-unh-u-gotcha | cycle-unh-limerick | 0 | 0.0 | 0 | 5 |
| cycle-unk-devoted | cycle-unk-devoted |  | 0 | 0.0 | 0 | 5 |
| cycle-unk-vegas | cycle-unk-vegas |  | 0 | 0.0 | 0 | 4 |
| cycle-unspeakable | cycle-unspeakable |  | 0 | 0.0 | 0 | 4 |
| cycle-usg-2-cycling-land | cycle-usg-2-cycling-land |  | 0 | 0.0 | 0 | 6 |
| cycle-usg-embrace | cycle-usg-embrace |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-enemy-backward-hate | cycle-usg-enemy-backward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-enemy-forward-hate | cycle-usg-enemy-forward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-enemy-hate | cycle-usg-enemy-hate |  | 0 | 0.0 | 0 | 10 |
| cycle-usg-legendary-land | cycle-usg-legendary-land |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-perpetual-aura | cycle-usg-perpetual-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-r-growing-enchant | cycle-usg-r-growing-enchant |  | 0 | 0.0 | 0 | 5 |
| cycle-usg-rune-protection | cycle-usg-rune-protection |  | 0 | 0.0 | 0 | 7 |
| cycle-usg-u-growing-enchant | cycle-usg-u-growing-enchant |  | 0 | 0.0 | 0 | 5 |
| cycle-ust-dice-host | cycle-ust-dice-host |  | 0 | 0.0 | 0 | 5 |
| cycle-ust-flavor-variant | cycle-ust-flavor-variant |  | 0 | 0.0 | 0 | 5 |
| cycle-ust-functional-variant | cycle-ust-functional-variant |  | 0 | 0.0 | 0 | 36 |
| cycle-ust-m-contraption | cycle-ust-m-contraption |  | 0 | 0.0 | 0 | 5 |
| cycle-ust-outside-assistance | cycle-ust-outside-assistance |  | 0 | 0.0 | 0 | 5 |
| cycle-ust-u-watermark-matters | cycle-ust-u-watermark-matters |  | 0 | 0.0 | 0 | 5 |
| cycle-verge | cycle-verge |  | 0 | 0.0 | 0 | 10 |
| cycle-vis-charm | cycle-vis-charm |  | 0 | 0.0 | 0 | 5 |
| cycle-vis-chimera | cycle-vis-chimera |  | 0 | 0.0 | 0 | 4 |
| cycle-vis-enemy-backward-hate | cycle-vis-enemy-backward-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-vis-karoo-land | cycle-vis-karoo-land |  | 0 | 0.0 | 0 | 5 |
| cycle-vma-r-two-color | cycle-vma-r-two-color |  | 0 | 0.0 | 0 | 10 |
| cycle-voc-soulbond | cycle-voc-soulbond |  | 0 | 0.0 | 0 | 5 |
| cycle-voice-angel | cycle-voice-angel |  | 0 | 0.0 | 0 | 6 |
| cycle-vow-c-typal-boost | cycle-vow-c-typal-boost |  | 0 | 0.0 | 0 | 5 |
| cycle-vow-cemetery | cycle-vow-cemetery |  | 0 | 0.0 | 0 | 5 |
| cycle-vow-draft-signpost | cycle-vow-draft-signpost | cycle-vow-signpost | 0 | 0.0 | 0 | 10 |
| cycle-vow-enemy-cleave | cycle-vow-enemy-cleave |  | 0 | 0.0 | 0 | 5 |
| cycle-vow-m-tdfc | cycle-vow-m-tdfc | cycle-vow-m-ndfc | 0 | 0.0 | 0 | 5 |
| cycle-vow-slowland | cycle-vow-slowland |  | 0 | 0.0 | 0 | 5 |
| cycle-vow-typal-hate | cycle-vow-typal-hate |  | 0 | 0.0 | 0 | 5 |
| cycle-war-bond | cycle-war-bond |  | 0 | 0.0 | 0 | 5 |
| cycle-war-color-artifact | cycle-war-color-artifact |  | 0 | 0.0 | 0 | 5 |
| cycle-war-draft-signpost | cycle-war-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-war-gatewatch | cycle-war-gatewatch |  | 0 | 0.0 | 0 | 5 |
| cycle-war-god | cycle-war-god |  | 0 | 0.0 | 0 | 5 |
| cycle-war-hybrid-planeswalker | cycle-war-hybrid-planeswalker |  | 0 | 0.0 | 0 | 10 |
| cycle-war-r-two-color | cycle-war-r-two-color |  | 0 | 0.0 | 0 | 20 |
| cycle-war-ravnican-legend | cycle-war-ravnican-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-war-triumph | cycle-war-triumph |  | 0 | 0.0 | 0 | 5 |
| cycle-war-u-planeswalker | cycle-war-u-planeswalker |  | 0 | 0.0 | 0 | 10 |
| cycle-war-u-two-color-spell | cycle-war-u-two-color-spell |  | 0 | 0.0 | 0 | 10 |
| cycle-woc-court | cycle-woc-court |  | 0 | 0.0 | 0 | 5 |
| cycle-woe-boon | cycle-woe-boon |  | 0 | 0.0 | 0 | 3 |
| cycle-woe-r-2c-adventurer | cycle-woe-r-2c-adventurer |  | 0 | 0.0 | 0 | 10 |
| cycle-woe-r-two-color | cycle-woe-r-two-color |  | 0 | 0.0 | 0 | 5 |
| cycle-woe-restless-land | cycle-woe-restless-land |  | 0 | 0.0 | 0 | 5 |
| cycle-woe-u-2c-adventurer | cycle-woe-u-2c-adventurer |  | 0 | 0.0 | 0 | 10 |
| cycle-woe-u-saga | cycle-woe-u-saga |  | 0 | 0.0 | 0 | 5 |
| cycle-woe-virtue | cycle-woe-virtue |  | 0 | 0.0 | 0 | 5 |
| cycle-wth-sac-aura | cycle-wth-sac-aura |  | 0 | 0.0 | 0 | 5 |
| cycle-wwk-creatureland | cycle-wwk-creatureland |  | 0 | 0.0 | 0 | 5 |
| cycle-xln-c-explorer | cycle-xln-c-explorer |  | 0 | 0.0 | 0 | 5 |
| cycle-xln-dino-avatar | cycle-xln-dino-avatar |  | 0 | 0.0 | 0 | 3 |
| cycle-xln-draft-signpost | cycle-xln-draft-signpost |  | 0 | 0.0 | 0 | 8 |
| cycle-xln-keeper | cycle-xln-keeper |  | 0 | 0.0 | 0 | 5 |
| cycle-xln-legendary-transform | cycle-xln-legendary-transform |  | 0 | 0.0 | 0 | 5 |
| cycle-xln-m-legend | cycle-xln-m-legend |  | 0 | 0.0 | 0 | 4 |
| cycle-xln-sun-aspect | cycle-xln-sun-aspect |  | 0 | 0.0 | 0 | 3 |
| cycle-yfra-stx-student | cycle-yfra-stx-student |  | 0 | 0.0 | 0 | 5 |
| cycle-ylci-typal-seek | cycle-ylci-typal-seek |  | 0 | 0.0 | 0 | 3 |
| cycle-ymkm-incorporate | cycle-ymkm-incorporate |  | 0 | 0.0 | 0 | 5 |
| cycle-yneo-costs-2-less | cycle-yneo-costs-2-less |  | 0 | 0.0 | 0 | 3 |
| cycle-yotj-collector | cycle-yotj-collector |  | 0 | 0.0 | 0 | 5 |
| cycle-young-planeswalker | cycle-young-planeswalker |  | 0 | 0.0 | 0 | 2 |
| cycle-ywoe-little-pig | cycle-ywoe-little-pig |  | 0 | 0.0 | 0 | 3 |
| cycle-zen-ascension | cycle-zen-ascension |  | 0 | 0.0 | 0 | 5 |
| cycle-zen-fetchland | cycle-zen-fetchland |  | 0 | 0.0 | 0 | 5 |
| cycle-zen-namedland | cycle-zen-namedland |  | 0 | 0.0 | 0 | 5 |
| cycle-zen-quest | cycle-zen-quest |  | 0 | 0.0 | 0 | 5 |
| cycle-zen-r-ally | cycle-zen-r-ally |  | 0 | 0.0 | 0 | 5 |
| cycle-zen-u-ally | cycle-zen-u-ally |  | 0 | 0.0 | 0 | 5 |
| cycle-zendikar-creatureland | cycle-zendikar-creatureland |  | 0 | 0.0 | 0 | 10 |
| cycle-znc-face-commander | cycle-znc-face-commander |  | 0 | 0.0 | 0 | 2 |
| cycle-znr-boltland | cycle-znr-boltland |  | 0 | 0.0 | 0 | 5 |
| cycle-znr-draft-signpost | cycle-znr-draft-signpost |  | 0 | 0.0 | 0 | 10 |
| cycle-znr-expeditioner | cycle-znr-expeditioner |  | 0 | 0.0 | 0 | 4 |
| cycle-znr-inscription | cycle-znr-inscription |  | 0 | 0.0 | 0 | 3 |
| cycle-znr-m-mono-creature | cycle-znr-m-mono-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-znr-m-mono-legend | cycle-znr-m-mono-legend |  | 0 | 0.0 | 0 | 5 |
| cycle-znr-multiclass-creature | cycle-znr-multiclass-creature |  | 0 | 0.0 | 0 | 3 |
| cycle-znr-pathway | cycle-znr-pathway |  | 0 | 0.0 | 0 | 6 |
| cycle-znr-r-mdfc | cycle-znr-r-mdfc |  | 0 | 0.0 | 0 | 5 |
| cycle-znr-relic | cycle-znr-relic |  | 0 | 0.0 | 0 | 4 |
| cycle-znr-two-color-legend | cycle-znr-two-color-legend |  | 0 | 0.0 | 0 | 10 |
| cycle-znr-u-mdfc-creature | cycle-znr-u-mdfc-creature |  | 0 | 0.0 | 0 | 5 |
| cycle-zodiac-creature | cycle-zodiac-creature |  | 0 | 0.0 | 0 | 12 |
| cycling-non-mana | cycling-non-mana |  | 0 | 0.0 | 0 | 2 |
| damage-increaser | damage increaser |  | 0 | 0.0 | 0 | 33 |
| damage-prevention-permanent | damage prevention-permanent |  | 0 | 0.0 | 0 | 3 |
| damage-redirection | damage redirection | redirect damage;damage deflection | 0 | 0.0 | 0 | 73 |
| damage-stays | damage stays |  | 0 | 0.0 | 0 | 7 |
| day/night | day/night |  | 0 | 0.0 | 0 | 53 |
| deanimate-self | deanimate self |  | 0 | 0.0 | 0 | 125 |
| deathtouch-counter | deathtouch counter |  | 0 | 0.0 | 0 | 20 |
| deathtouch-to-planeswalkers | deathtouch to planeswalkers | planeswalker deathtouch | 0 | 0.0 | 0 | 4 |
| decayed-counter | decayed counter |  | 0 | 0.0 | 0 | 1 |
| deck-requirement | deck requirement |  | 0 | 0.0 | 0 | 28 |
| dehydration-with-set-mechanic | dehydration with set mechanic |  | 0 | 0.0 | 0 | 17 |
| delayed-cantrip | delayed cantrip |  | 0 | 0.0 | 0 | 59 |
| delayed-payment | delayed payment |  | 0 | 0.0 | 0 | 7 |
| delayed-replacement-effect | delayed replacement effect |  | 0 | 0.0 | 0 | 34 |
| delve | delve |  | 0 | 0.0 | 0 | 31 |
| demilich-effect | demilich effect |  | 0 | 0.0 | 0 | 37 |
| depletion-land | depletion land |  | 0 | 0.0 | 0 | 10 |
| deprecated-legend-restriction | deprecated legend restriction |  | 0 | 0.0 | 0 | 3 |
| deprecated-p/t-counter | deprecated p/t counter |  | 0 | 0.0 | 0 | 39 |
| deprecated-untapped-artifact | deprecated untapped artifact |  | 0 | 0.0 | 0 | 5 |
| deprecated-wall-restriction | deprecated wall restriction |  | 0 | 0.0 | 0 | 4 |
| dexterity | dexterity | physical interaction | 0 | 0.0 | 0 | 67 |
| dice-reroll | dice reroll |  | 0 | 0.0 | 0 | 5 |
| dice-roll | dice roll | dice | 0 | 0.0 | 0 | 197 |
| differently-named-lands-matter | differently named lands matter | strange new worlds | 0 | 0.0 | 0 | 28 |
| digital-replacement | digital replacement |  | 0 | 0.0 | 0 | 1 |
| digital-to-paper | digital to paper |  | 0 | 0.0 | 0 | 23 |
| digital-only-mechanics | digital-only mechanics | arena-only mechanics | 0 | 0.0 | 0 | 630 |
| discard-outlet-artifact | discard outlet-artifact |  | 0 | 0.0 | 0 | 6 |
| discard-outlet-creature | discard outlet-creature |  | 0 | 0.0 | 0 | 28 |
| discard-outlet-last-drawn | discard outlet-last drawn |  | 0 | 0.0 | 0 | 5 |
| discard-outlet-legendary | discard outlet-legendary |  | 0 | 0.0 | 0 | 5 |
| discard-outlet-nonland | discard outlet-nonland |  | 0 | 0.0 | 0 | 7 |
| discard-outlet-random | discard outlet-random |  | 0 | 0.0 | 0 | 49 |
| discard-to-library | discard to library | discard-library | 0 | 0.0 | 0 | 22 |
| discard-symmetrical | discard-symmetrical |  | 0 | 0.0 | 0 | 29 |
| distinct-echo-cost | distinct echo cost |  | 0 | 0.0 | 0 | 11 |
| disturb | disturb |  | 0 | 0.0 | 0 | 25 |
| divides-battlefield | divides battlefield |  | 0 | 0.0 | 0 | 4 |
| dnd-book | dnd book |  | 0 | 0.0 | 0 | 8 |
| dnd-item | dnd item | d&d item | 0 | 0.0 | 0 | 55 |
| dnd-mechanic | dnd mechanic | d&d mechanic;dnd feature;d&d feature | 0 | 0.0 | 0 | 75 |
| dnd-monster | dnd monster | d&d monster | 0 | 0.0 | 0 | 89 |
| doctor-who-episode-saga | doctor who episode saga | dr who episode saga | 0 | 0.0 | 0 | 19 |
| doesn't-untap | doesn't untap |  | 0 | 0.0 | 0 | 44 |
| dolmen-ability | dolmen ability | gives hope | 0 | 0.0 | 0 | 9 |
| donate-mana | donate mana |  | 0 | 0.0 | 0 | 42 |
| donate-rampant-growth | donate rampant growth |  | 0 | 0.0 | 0 | 27 |
| double-strike-counter | double strike counter |  | 0 | 0.0 | 0 | 7 |
| draft-matters | draft matters |  | 0 | 0.0 | 0 | 28 |
| drain-strength | drain strength |  | 0 | 0.0 | 0 | 27 |
| draw-to-seven | draw to seven |  | 0 | 0.0 | 0 | 6 |
| earthbend | earthbend |  | 0 | 0.0 | 0 | 36 |
| eat-food | eat food |  | 0 | 0.0 | 0 | 4 |
| eldrazi-titan | eldrazi titan |  | 0 | 0.0 | 0 | 9 |
| embalm-token | embalm token |  | 0 | 0.0 | 0 | 15 |
| emerge | emerge |  | 0 | 0.0 | 0 | 21 |
| emerge-from-artifact | emerge-from-artifact |  | 0 | 0.0 | 0 | 2 |
| emerge-from-creature | emerge-from-creature |  | 0 | 0.0 | 0 | 19 |
| eminence | eminence |  | 0 | 0.0 | 0 | 12 |
| empty-library | empty library |  | 0 | 0.0 | 0 | 9 |
| enchantment-engine | enchantment engine | enchantress | 0 | 0.0 | 0 | 22 |
| enchantmentfall | enchantmentfall | constellation | 0 | 0.0 | 0 | 73 |
| enchantmentize | enchantmentize |  | 0 | 0.0 | 0 | 37 |
| end-turn | end turn |  | 0 | 0.0 | 0 | 9 |
| energy-generator | energy generator |  | 0 | 0.0 | 0 | 137 |
| energy-increaser | energy increaser |  | 0 | 0.0 | 0 | 6 |
| enters-and-leaves-trigger-self | enters-and-leaves-trigger-self |  | 0 | 0.0 | 0 | 15 |
| equipless-equipment | equipless equipment |  | 0 | 0.0 | 0 | 6 |
| etb-untapper | etb-untapper |  | 0 | 0.0 | 0 | 9 |
| eternalize | eternalize |  | 0 | 0.0 | 0 | 8 |
| eternalize-token | eternalize token |  | 0 | 0.0 | 0 | 13 |
| ethereal-armor | ethereal armor |  | 0 | 0.0 | 0 | 18 |
| even/odd-matters | even/odd matters |  | 0 | 0.0 | 0 | 26 |
| exalted-counter | exalted counter |  | 0 | 0.0 | 0 | 1 |
| exchange-dice-roll | exchange dice roll |  | 0 | 0.0 | 0 | 2 |
| exhaust | exhaust |  | 0 | 0.0 | 0 | 105 |
| exile-with-tax | exile with tax |  | 0 | 0.0 | 0 | 20 |
| exile-self-dfc-transform | exile-self-dfc-transform | flicker-dfc-transform | 0 | 0.0 | 0 | 90 |
| exiletouch | exiletouch |  | 0 | 0.0 | 0 | 5 |
| exo-storyline-in-cards | exo-storyline-in-cards |  | 0 | 0.0 | 0 | 14 |
| expansion-sweeper | expansion sweeper |  | 0 | 0.0 | 0 | 5 |
| expertise | expertise |  | 0 | 0.0 | 0 | 22 |
| external-prop | external prop | prop | 0 | 0.0 | 0 | 22 |
| extra-draft | extra draft |  | 0 | 0.0 | 0 | 5 |
| extra-draw-step | extra draw step |  | 0 | 0.0 | 0 | 4 |
| extra-turn | extra turn |  | 0 | 0.0 | 0 | 65 |
| extra-untap | extra untap |  | 0 | 0.0 | 0 | 114 |
| extra-upkeep | extra upkeep | additional upkeep | 0 | 0.0 | 0 | 7 |
| face-up-face-down-effects | face-up-face-down-effects | face-down-face-up-effects | 0 | 0.0 | 0 | 208 |
| fallout-perk-name | fallout perk name |  | 0 | 0.0 | 0 | 6 |
| fallout-vault-saga | fallout vault saga |  | 0 | 0.0 | 0 | 8 |
| fateseal | fateseal |  | 0 | 0.0 | 0 | 20 |
| filterland | filterland |  | 0 | 0.0 | 0 | 74 |
| fire-drake | fire drake |  | 0 | 0.0 | 0 | 5 |
| first-strike-counter | first strike counter |  | 0 | 0.0 | 0 | 16 |
| flagbearer | flagbearer |  | 0 | 0.0 | 0 | 4 |
| flavor-matters | flavor matters |  | 0 | 0.0 | 0 | 3 |
| flavor-text-matters | flavor text matters |  | 0 | 0.0 | 0 | 14 |
| flicker-nonenchantment | flicker-nonenchantment |  | 0 | 0.0 | 0 | 1 |
| flicker-nonland | flicker-nonland |  | 0 | 0.0 | 0 | 14 |
| flicker-self | flicker-self |  | 0 | 0.0 | 0 | 46 |
| flicker-vehicle | flicker-vehicle |  | 0 | 0.0 | 0 | 1 |
| flying-counter | flying counter |  | 0 | 0.0 | 0 | 44 |
| forestfall | forestfall |  | 0 | 0.0 | 0 | 9 |
| form | form |  | 0 | 0.0 | 0 | 9 |
| format-matters | format matters |  | 0 | 0.0 | 0 | 9 |
| four-loyalty-abilities | four loyalty abilities |  | 0 | 0.0 | 0 | 12 |
| four-plus-creature-types | four plus creature types |  | 0 | 0.0 | 0 | 26 |
| fourth-spell-matters | fourth spell matters |  | 0 | 0.0 | 0 | 3 |
| fractional-life/damage | fractional life/damage |  | 0 | 0.0 | 0 | 10 |
| fractional-power/toughness | fractional power/toughness |  | 0 | 0.0 | 0 | 12 |
| freeze-artifact | freeze-artifact | stun-artifact | 0 | 0.0 | 0 | 11 |
| freeze-land | freeze-land | stun-land | 0 | 0.0 | 0 | 10 |
| freeze-nonland | freeze-nonland | stun-nonland | 0 | 0.0 | 0 | 6 |
| front-card | front-card |  | 0 | 0.0 | 0 | 291 |
| frost-armor | frost armor |  | 0 | 0.0 | 0 | 15 |
| fulfilled-futureshift | fulfilled futureshift |  | 0 | 0.0 | 0 | 13 |
| functional-art | functional art |  | 0 | 0.0 | 0 | 6 |
| fungusaur-effect | fungusaur effect |  | 0 | 0.0 | 0 | 12 |
| future-sight-engine | future sight engine |  | 0 | 0.0 | 0 | 10 |
| gains-absorb | gains absorb |  | 0 | 0.0 | 0 | 1 |
| gains-afflict | gains afflict |  | 0 | 0.0 | 0 | 2 |
| gains-annihilator | gains annihilator |  | 0 | 0.0 | 0 | 3 |
| gains-banding | gains banding |  | 0 | 0.0 | 0 | 10 |
| gains-battle-cry | gains battle cry |  | 0 | 0.0 | 0 | 2 |
| gains-bushido | gains bushido |  | 0 | 0.0 | 0 | 3 |
| gains-cascade | gains cascade |  | 0 | 0.0 | 0 | 1 |
| gains-changeling | gains changeling |  | 0 | 0.0 | 0 | 1 |
| gains-daunt | gains daunt |  | 0 | 0.0 | 0 | 1 |
| gains-defender | gains defender |  | 0 | 0.0 | 0 | 9 |
| gains-dethrone | gains dethrone |  | 0 | 0.0 | 0 | 1 |
| gains-devoid | gains devoid |  | 0 | 0.0 | 0 | 2 |
| gains-double-strike | gains double strike |  | 0 | 0.0 | 0 | 105 |
| gains-exalted | gains exalted |  | 0 | 0.0 | 0 | 2 |
| gains-exploit | gains exploit |  | 0 | 0.0 | 0 | 1 |
| gains-fear | gains fear |  | 0 | 0.0 | 0 | 18 |
| gains-firebending | gains firebending |  | 0 | 0.0 | 0 | 2 |
| gains-flanking | gains flanking |  | 0 | 0.0 | 0 | 2 |
| gains-for-mirrodin! | gains for mirrodin! |  | 0 | 0.0 | 0 | 1 |
| gains-forestwalk | gains forestwalk |  | 0 | 0.0 | 0 | 7 |
| gains-frenzy | gains frenzy |  | 0 | 0.0 | 0 | 1 |
| gains-horsemanship | gains horsemanship |  | 0 | 0.0 | 0 | 2 |
| gains-ingest | gains ingest |  | 0 | 0.0 | 0 | 8 |
| gains-islandwalk | gains islandwalk |  | 0 | 0.0 | 0 | 3 |
| gains-landwalk | gains landwalk |  | 0 | 0.0 | 0 | 22 |
| gains-living-weapon | gains living weapon |  | 0 | 0.0 | 0 | 1 |
| gains-melee | gains melee |  | 0 | 0.0 | 0 | 1 |
| gains-mountainwalk | gains mountainwalk |  | 0 | 0.0 | 0 | 2 |
| gains-myriad | gains myriad |  | 0 | 0.0 | 0 | 4 |
| gains-poisonous | gains poisonous |  | 0 | 0.0 | 0 | 2 |
| gains-protection | gains protection |  | 0 | 0.0 | 0 | 61 |
| gains-provoke | gains provoke |  | 0 | 0.0 | 0 | 2 |
| gains-prowess | gains prowess |  | 0 | 0.0 | 0 | 2 |
| gains-rampage | gains rampage |  | 0 | 0.0 | 0 | 5 |
| gains-reach | gains reach |  | 0 | 0.0 | 0 | 34 |
| gains-renown | gains renown |  | 0 | 0.0 | 0 | 1 |
| gains-shadow | gains shadow |  | 0 | 0.0 | 0 | 7 |
| gains-shroud | gains shroud |  | 0 | 0.0 | 0 | 27 |
| gains-skulk | gains skulk |  | 0 | 0.0 | 0 | 21 |
| gains-soulshift | gains soulshift |  | 0 | 0.0 | 0 | 1 |
| gains-split-second | gains split second |  | 0 | 0.0 | 0 | 1 |
| gains-suspend | gains suspend |  | 0 | 0.0 | 0 | 3 |
| gains-swampwalk | gains swampwalk |  | 0 | 0.0 | 0 | 4 |
| gains-tantrum | gains tantrum |  | 0 | 0.0 | 0 | 1 |
| gains-toxic | gains toxic |  | 0 | 0.0 | 0 | 2 |
| gains-training | gains training |  | 0 | 0.0 | 0 | 1 |
| gains-umbra-armor | gains umbra armor |  | 0 | 0.0 | 0 | 1 |
| gains-undying | gains undying |  | 0 | 0.0 | 0 | 1 |
| gains-vanishing | gains vanishing |  | 0 | 0.0 | 0 | 2 |
| gains-ward | gains ward |  | 0 | 0.0 | 0 | 16 |
| gains-wither | gains wither |  | 0 | 0.0 | 0 | 6 |
| gamble | gamble |  | 0 | 0.0 | 0 | 7 |
| gatewatch-oath | gatewatch oath |  | 0 | 0.0 | 0 | 8 |
| gender-matters | gender matters |  | 0 | 0.0 | 0 | 1 |
| genesis-effect | genesis effect |  | 0 | 0.0 | 0 | 56 |
| gifts-ungiven | gifts ungiven |  | 0 | 0.0 | 0 | 17 |
| gives-absorb | gives absorb |  | 0 | 0.0 | 0 | 1 |
| gives-adventure | gives adventure |  | 0 | 0.0 | 0 | 1 |
| gives-affinity | gives affinity |  | 0 | 0.0 | 0 | 17 |
| gives-afflict | gives afflict |  | 0 | 0.0 | 0 | 8 |
| gives-afterlife | gives afterlife |  | 0 | 0.0 | 0 | 2 |
| gives-annihilator | gives annihilator |  | 0 | 0.0 | 0 | 7 |
| gives-assist | gives assist |  | 0 | 0.0 | 0 | 1 |
| gives-banding | gives banding |  | 0 | 0.0 | 0 | 14 |
| gives-basic-landcycling | gives basic landcycling |  | 0 | 0.0 | 0 | 1 |
| gives-battle-cry | gives battle cry |  | 0 | 0.0 | 0 | 2 |
| gives-beam-me-up | gives beam me up |  | 0 | 0.0 | 0 | 1 |
| gives-blitz | gives blitz |  | 0 | 0.0 | 0 | 3 |
| gives-bloodthirst | gives bloodthirst |  | 0 | 0.0 | 0 | 2 |
| gives-bushido | gives bushido |  | 0 | 0.0 | 0 | 2 |
| gives-cascade | gives cascade |  | 0 | 0.0 | 0 | 18 |
| gives-casualty | gives casualty |  | 0 | 0.0 | 0 | 4 |
| gives-charge-counter | gives charge counter |  | 0 | 0.0 | 0 | 21 |
| gives-convoke | gives convoke |  | 0 | 0.0 | 0 | 14 |
| gives-cumulative-upkeep | gives cumulative upkeep |  | 0 | 0.0 | 0 | 5 |
| gives-cycling | gives cycling |  | 0 | 0.0 | 0 | 6 |
| gives-daunt | gives daunt |  | 0 | 0.0 | 0 | 8 |
| gives-deathtouch-noncreature | gives deathtouch noncreature |  | 0 | 0.0 | 0 | 2 |
| gives-decayed | gives decayed |  | 0 | 0.0 | 0 | 3 |
| gives-delve | gives delve |  | 0 | 0.0 | 0 | 1 |
| gives-demonstrate | gives demonstrate |  | 0 | 0.0 | 0 | 6 |
| gives-dethrone | gives dethrone |  | 0 | 0.0 | 0 | 1 |
| gives-devoid | gives devoid |  | 0 | 0.0 | 0 | 2 |
| gives-devour | gives devour |  | 0 | 0.0 | 0 | 1 |
| gives-disguise | gives disguise |  | 0 | 0.0 | 0 | 1 |
| gives-double-team | gives double team |  | 0 | 0.0 | 0 | 5 |
| gives-dredge | gives dredge |  | 0 | 0.0 | 0 | 1 |
| gives-echo | gives echo |  | 0 | 0.0 | 0 | 1 |
| gives-embalm | gives embalm |  | 0 | 0.0 | 0 | 2 |
| gives-emerge | gives emerge |  | 0 | 0.0 | 0 | 1 |
| gives-encore | gives encore |  | 0 | 0.0 | 0 | 4 |
| gives-epic | gives epic |  | 0 | 0.0 | 0 | 1 |
| gives-escape | gives escape |  | 0 | 0.0 | 0 | 7 |
| gives-evoke | gives evoke |  | 0 | 0.0 | 0 | 2 |
| gives-evolve | gives evolve |  | 0 | 0.0 | 0 | 3 |
| gives-exalted | gives exalted |  | 0 | 0.0 | 0 | 11 |
| gives-exploit | gives exploit |  | 0 | 0.0 | 0 | 2 |
| gives-extort | gives extort |  | 0 | 0.0 | 0 | 1 |
| gives-fabricate | gives fabricate |  | 0 | 0.0 | 0 | 1 |
| gives-firebending | gives firebending |  | 0 | 0.0 | 0 | 4 |
| gives-flanking | gives flanking |  | 0 | 0.0 | 0 | 6 |
| gives-flash | gives flash |  | 0 | 0.0 | 0 | 64 |
| gives-flashback | gives flashback |  | 0 | 0.0 | 0 | 19 |
| gives-forestwalk | gives forestwalk |  | 0 | 0.0 | 0 | 11 |
| gives-foretell | gives foretell | grants foretell | 0 | 0.0 | 0 | 4 |
| gives-fossilize | gives fossilize |  | 0 | 0.0 | 0 | 1 |
| gives-freerunning | gives freerunning |  | 0 | 0.0 | 0 | 1 |
| gives-frenzy | gives frenzy |  | 0 | 0.0 | 0 | 1 |
| gives-harmonize | gives harmonize |  | 0 | 0.0 | 0 | 1 |
| gives-high-flying | gives high flying |  | 0 | 0.0 | 0 | 4 |
| gives-horsemanship | gives horsemanship |  | 0 | 0.0 | 0 | 10 |
| gives-improvise | gives improvise |  | 0 | 0.0 | 0 | 5 |
| gives-ingest | gives ingest |  | 0 | 0.0 | 0 | 13 |
| gives-intimidate | gives intimidate |  | 0 | 0.0 | 0 | 18 |
| gives-islandwalk | gives islandwalk |  | 0 | 0.0 | 0 | 11 |
| gives-jump-start | gives jump-start |  | 0 | 0.0 | 0 | 3 |
| gives-landwalk | gives landwalk |  | 0 | 0.0 | 0 | 46 |
| gives-lifelink-noncreature | gives lifelink noncreature |  | 0 | 0.0 | 0 | 10 |
| gives-living-weapon | gives living weapon |  | 0 | 0.0 | 0 | 1 |
| gives-loyalty-ability | gives loyalty ability |  | 0 | 0.0 | 0 | 16 |
| gives-madness | gives madness |  | 0 | 0.0 | 0 | 1 |
| gives-mayhem | gives mayhem |  | 0 | 0.0 | 0 | 1 |
| gives-melee | gives melee |  | 0 | 0.0 | 0 | 8 |
| gives-mentor | gives mentor |  | 0 | 0.0 | 0 | 3 |
| gives-miracle | gives miracle |  | 0 | 0.0 | 0 | 4 |
| gives-mobilize | gives mobilize |  | 0 | 0.0 | 0 | 2 |
| gives-modular | gives modular |  | 0 | 0.0 | 0 | 1 |
| gives-mountainwalk | gives mountainwalk |  | 0 | 0.0 | 0 | 6 |
| gives-myriad | gives myriad |  | 0 | 0.0 | 0 | 9 |
| gives-nimble | gives nimble |  | 0 | 0.0 | 0 | 4 |
| gives-ninjutsu | gives ninjutsu |  | 0 | 0.0 | 0 | 1 |
| gives-offspring | gives offspring |  | 0 | 0.0 | 0 | 2 |
| gives-outlast | gives outlast |  | 0 | 0.0 | 0 | 3 |
| gives-phasing | gives phasing |  | 0 | 0.0 | 0 | 4 |
| gives-plainswalk | gives plainswalk |  | 0 | 0.0 | 0 | 1 |
| gives-player-ability | gives player ability |  | 0 | 0.0 | 0 | 45 |
| gives-player-hexproof | gives player hexproof |  | 0 | 0.0 | 0 | 24 |
| gives-player-protection | gives player protection |  | 0 | 0.0 | 0 | 14 |
| gives-player-shroud | gives player shroud |  | 0 | 0.0 | 0 | 5 |
| gives-plot | gives plot |  | 0 | 0.0 | 0 | 6 |
| gives-provoke | gives provoke |  | 0 | 0.0 | 0 | 3 |
| gives-prowess | gives prowess | grants prowess | 0 | 0.0 | 0 | 8 |
| gives-prowl | gives prowl |  | 0 | 0.0 | 0 | 1 |
| gives-rampage | gives rampage |  | 0 | 0.0 | 0 | 7 |
| gives-read-ahead | gives read ahead |  | 0 | 0.0 | 0 | 1 |
| gives-rebound | gives rebound |  | 0 | 0.0 | 0 | 5 |
| gives-relentless | gives relentless |  | 0 | 0.0 | 0 | 1 |
| gives-renown | gives renown |  | 0 | 0.0 | 0 | 1 |
| gives-replicate | gives replicate |  | 0 | 0.0 | 0 | 5 |
| gives-retrace | gives retrace |  | 0 | 0.0 | 0 | 4 |
| gives-riot | gives riot |  | 0 | 0.0 | 0 | 4 |
| gives-ripple | gives ripple |  | 0 | 0.0 | 0 | 1 |
| gives-saddle | gives saddle |  | 0 | 0.0 | 0 | 1 |
| gives-scavenge | gives scavenge |  | 0 | 0.0 | 0 | 3 |
| gives-shadow | gives shadow |  | 0 | 0.0 | 0 | 14 |
| gives-shroud | gives shroud |  | 0 | 0.0 | 0 | 49 |
| gives-skulk | gives skulk |  | 0 | 0.0 | 0 | 58 |
| gives-sneak | gives sneak |  | 0 | 0.0 | 0 | 2 |
| gives-spectacle | gives spectacle |  | 0 | 0.0 | 0 | 1 |
| gives-split-second | gives split second |  | 0 | 0.0 | 0 | 5 |
| gives-squad | gives squad |  | 0 | 0.0 | 0 | 1 |
| gives-stalking | gives stalking |  | 0 | 0.0 | 0 | 13 |
| gives-storm | gives storm |  | 0 | 0.0 | 0 | 6 |
| gives-sunburst | gives sunburst |  | 0 | 0.0 | 0 | 3 |
| gives-super-haste | gives super haste |  | 0 | 0.0 | 0 | 1 |
| gives-suspend | gives suspend |  | 0 | 0.0 | 0 | 18 |
| gives-swampwalk | gives swampwalk |  | 0 | 0.0 | 0 | 7 |
| gives-tantrum | gives tantrum |  | 0 | 0.0 | 0 | 2 |
| gives-thoughtweft | gives thoughtweft |  | 0 | 0.0 | 0 | 1 |
| gives-townwalk | gives townwalk |  | 0 | 0.0 | 0 | 1 |
| gives-toxic | gives toxic |  | 0 | 0.0 | 0 | 9 |
| gives-training | gives training |  | 0 | 0.0 | 0 | 2 |
| gives-triple-strike | gives triple strike |  | 0 | 0.0 | 0 | 1 |
| gives-umbra-armor | gives umbra armor |  | 0 | 0.0 | 0 | 1 |
| gives-undying | gives undying |  | 0 | 0.0 | 0 | 4 |
| gives-unearth | gives unearth |  | 0 | 0.0 | 0 | 9 |
| gives-unleash | gives unleash |  | 0 | 0.0 | 0 | 1 |
| gives-unstoppable | gives unstoppable |  | 0 | 0.0 | 0 | 8 |
| gives-warp | gives warp |  | 0 | 0.0 | 0 | 3 |
| gives-web-slinging | gives web-slinging |  | 0 | 0.0 | 0 | 1 |
| gives-wither-noncreature | gives wither noncreature |  | 0 | 0.0 | 0 | 1 |
| grafted-skullcap | grafted skullcap |  | 0 | 0.0 | 0 | 7 |
| graveyard-fuel-artifact | graveyard fuel-artifact |  | 0 | 0.0 | 0 | 30 |
| graveyard-fuel-enchantment | graveyard fuel-enchantment |  | 0 | 0.0 | 0 | 3 |
| graveyard-fuel-historic | graveyard fuel-historic |  | 0 | 0.0 | 0 | 2 |
| graveyard-fuel-instant | graveyard fuel-instant |  | 0 | 0.0 | 0 | 39 |
| graveyard-fuel-land | graveyard fuel-land |  | 0 | 0.0 | 0 | 8 |
| graveyard-fuel-legendary | graveyard fuel-legendary |  | 0 | 0.0 | 0 | 4 |
| graveyard-fuel-noncreature | graveyard fuel-noncreature |  | 0 | 0.0 | 0 | 3 |
| graveyard-fuel-nonland | graveyard fuel-nonland |  | 0 | 0.0 | 0 | 7 |
| graveyard-fuel-permanent | graveyard fuel-permanent |  | 0 | 0.0 | 0 | 4 |
| graveyard-fuel-saga | graveyard fuel-saga |  | 0 | 0.0 | 0 | 3 |
| graveyard-fuel-sorcery | graveyard fuel-sorcery |  | 0 | 0.0 | 0 | 37 |
| graveyard-order-matters | graveyard order matters |  | 0 | 0.0 | 0 | 23 |
| great-designer-search-3 | great-designer-search-3 |  | 0 | 0.0 | 0 | 10 |
| greatest-power-matters | greatest power matters |  | 0 | 0.0 | 0 | 6 |
| greed-ability | greed ability |  | 0 | 0.0 | 0 | 12 |
| grim-return | grim return | second sunrise | 0 | 0.0 | 0 | 17 |
| guest-designer | guest designer |  | 0 | 0.0 | 0 | 16 |
| gunk | gunk |  | 0 | 0.0 | 0 | 4 |
| half-mana | half mana |  | 0 | 0.0 | 0 | 6 |
| hand-size-decrease | hand size decrease |  | 0 | 0.0 | 0 | 15 |
| harmonic | harmonic |  | 0 | 0.0 | 0 | 25 |
| haste-counter | haste counter |  | 0 | 0.0 | 0 | 4 |
| hate-adventure | hate-adventure |  | 0 | 0.0 | 0 | 3 |
| hate-arcane | hate-arcane |  | 0 | 0.0 | 0 | 5 |
| hate-artifact-creature | hate-artifact-creature |  | 0 | 0.0 | 0 | 22 |
| hate-artifact-land | hate-artifact-land |  | 0 | 0.0 | 0 | 2 |
| hate-attraction | hate-attraction |  | 0 | 0.0 | 0 | 4 |
| hate-backup | hate-backup |  | 0 | 0.0 | 0 | 1 |
| hate-banding | hate-banding |  | 0 | 0.0 | 0 | 2 |
| hate-battle | hate-battle |  | 0 | 0.0 | 0 | 3 |
| hate-blood | hate-blood |  | 0 | 0.0 | 0 | 1 |
| hate-clue | hate-clue |  | 0 | 0.0 | 0 | 1 |
| hate-color-every | hate-color-every |  | 0 | 0.0 | 0 | 9 |
| hate-color-non-share | hate-color-non-share |  | 0 | 0.0 | 0 | 3 |
| hate-color-share | hate-color-share |  | 0 | 0.0 | 0 | 27 |
| hate-colored | hate-colored |  | 0 | 0.0 | 0 | 12 |
| hate-colorless | hate-colorless | colorless hate | 0 | 0.0 | 0 | 14 |
| hate-commander | hate-commander |  | 0 | 0.0 | 0 | 7 |
| hate-conspiracy | hate-conspiracy |  | 0 | 0.0 | 0 | 1 |
| hate-contraption | hate-contraption |  | 0 | 0.0 | 0 | 1 |
| hate-counters | hate-counters |  | 0 | 0.0 | 0 | 68 |
| hate-curse | hate-curse |  | 0 | 0.0 | 0 | 1 |
| hate-cycling | hate-cycling |  | 0 | 0.0 | 0 | 8 |
| hate-damaged | hate-damaged |  | 0 | 0.0 | 0 | 31 |
| hate-deathtouch | hate-deathtouch |  | 0 | 0.0 | 0 | 5 |
| hate-desert | hate-desert |  | 0 | 0.0 | 0 | 4 |
| hate-dice | hate-dice |  | 0 | 0.0 | 0 | 1 |
| hate-disturb | hate-disturb |  | 0 | 0.0 | 0 | 1 |
| hate-double-strike | hate-double-strike |  | 0 | 0.0 | 0 | 2 |
| hate-enchantment | hate-enchantment |  | 0 | 0.0 | 0 | 50 |
| hate-enchantment-creature | hate-enchantment-creature |  | 0 | 0.0 | 0 | 4 |
| hate-etb | hate-etb |  | 0 | 0.0 | 0 | 9 |
| hate-exile-cast | hate-exile-cast |  | 0 | 0.0 | 0 | 4 |
| hate-face-down | hate-face-down |  | 0 | 0.0 | 0 | 16 |
| hate-fear | hate-fear |  | 0 | 0.0 | 0 | 1 |
| hate-first-strike | hate-first-strike |  | 0 | 0.0 | 0 | 10 |
| hate-flanking | hate-flanking |  | 0 | 0.0 | 0 | 1 |
| hate-flash | hate-flash |  | 0 | 0.0 | 0 | 19 |
| hate-flashback | hate-flashback |  | 0 | 0.0 | 0 | 2 |
| hate-food | hate-food |  | 0 | 0.0 | 0 | 2 |
| hate-forest | hate-forest |  | 0 | 0.0 | 0 | 15 |
| hate-free-spell | hate-free-spell |  | 0 | 0.0 | 0 | 13 |
| hate-goad | hate-goad |  | 0 | 0.0 | 0 | 1 |
| hate-graveyard-cast | hate-graveyard-cast |  | 0 | 0.0 | 0 | 10 |
| hate-haste | hate-haste |  | 0 | 0.0 | 0 | 2 |
| hate-horsemanship | hate-horsemanship |  | 0 | 0.0 | 0 | 4 |
| hate-hybrid | hate-hybrid |  | 0 | 0.0 | 0 | 1 |
| hate-island | hate-island |  | 0 | 0.0 | 0 | 26 |
| hate-kicker | hate-kicker |  | 0 | 0.0 | 0 | 1 |
| hate-landwalk | hate-landwalk |  | 0 | 0.0 | 0 | 16 |
| hate-library-cast | hate-library-cast |  | 0 | 0.0 | 0 | 2 |
| hate-life-payment | hate-life-payment |  | 0 | 0.0 | 0 | 3 |
| hate-lifelink | hate-lifelink |  | 0 | 0.0 | 0 | 1 |
| hate-low-toughness | hate-low-toughness |  | 0 | 0.0 | 0 | 22 |
| hate-menace | hate-menace |  | 0 | 0.0 | 0 | 1 |
| hate-mm-counter | hate-mm-counter |  | 0 | 0.0 | 0 | 3 |
| hate-monocolor | hate-monocolor |  | 0 | 0.0 | 0 | 14 |
| hate-morph | hate-morph |  | 0 | 0.0 | 0 | 2 |
| hate-mountain | hate-mountain |  | 0 | 0.0 | 0 | 16 |
| hate-multicolor | hate-multicolor | hate-color-multi | 0 | 0.0 | 0 | 22 |
| hate-nonartifact | hate-nonartifact |  | 0 | 0.0 | 0 | 4 |
| hate-noncreature | hate-noncreature |  | 0 | 0.0 | 0 | 47 |
| hate-nonhand-cast | hate-nonhand-cast |  | 0 | 0.0 | 0 | 4 |
| hate-off-turn-cast | hate-off-turn-cast |  | 0 | 0.0 | 0 | 7 |
| hate-plains | hate-plains |  | 0 | 0.0 | 0 | 17 |
| hate-planeswalker-bolas | hate-planeswalker-bolas |  | 0 | 0.0 | 0 | 1 |
| hate-planeswalker-chandra | hate-planeswalker-chandra |  | 0 | 0.0 | 0 | 1 |
| hate-planeswalker-jace | hate-planeswalker-jace | hate-jace | 0 | 0.0 | 0 | 1 |
| hate-protection | hate-protection |  | 0 | 0.0 | 0 | 3 |
| hate-ramp | hate-ramp |  | 0 | 0.0 | 0 | 6 |
| hate-reach | hate-reach |  | 0 | 0.0 | 0 | 2 |
| hate-removal-sacrifice | hate-removal-sacrifice | hate-sacrifice | 0 | 0.0 | 0 | 33 |
| hate-room | hate-room |  | 0 | 0.0 | 0 | 1 |
| hate-saga | hate-saga |  | 0 | 0.0 | 0 | 1 |
| hate-scry | hate-scry |  | 0 | 0.0 | 0 | 1 |
| hate-shadow | hate-shadow |  | 0 | 0.0 | 0 | 12 |
| hate-shuffle | hate-shuffle |  | 0 | 0.0 | 0 | 4 |
| hate-snow | hate-snow |  | 0 | 0.0 | 0 | 19 |
| hate-spacecraft | hate-spacecraft |  | 0 | 0.0 | 0 | 5 |
| hate-speed | hate-speed |  | 0 | 0.0 | 0 | 1 |
| hate-splice | hate-splice |  | 0 | 0.0 | 0 | 1 |
| hate-storm | hate-storm |  | 0 | 0.0 | 0 | 18 |
| hate-surveil | hate-surveil |  | 0 | 0.0 | 0 | 1 |
| hate-suspect | hate-suspect |  | 0 | 0.0 | 0 | 5 |
| hate-suspend | hate-suspend |  | 0 | 0.0 | 0 | 7 |
| hate-swamp | hate-swamp |  | 0 | 0.0 | 0 | 18 |
| hate-token | hate-token | hate-token-creature | 0 | 0.0 | 0 | 34 |
| hate-town | hate-town |  | 0 | 0.0 | 0 | 1 |
| hate-toxic | hate-toxic |  | 0 | 0.0 | 0 | 1 |
| hate-transform | hate-transform |  | 0 | 0.0 | 0 | 2 |
| hate-trap | hate-trap |  | 0 | 0.0 | 0 | 1 |
| hate-treasure | hate-treasure |  | 0 | 0.0 | 0 | 2 |
| hate-tutor | hate-tutor |  | 0 | 0.0 | 0 | 17 |
| hate-typal-alien | hate-typal-alien |  | 0 | 0.0 | 0 | 1 |
| hate-typal-angel | hate-typal-angel | hate-tribal-angel | 0 | 0.0 | 0 | 2 |
| hate-typal-archon | hate-typal-archon |  | 0 | 0.0 | 0 | 1 |
| hate-typal-assassin | hate-typal-assassin |  | 0 | 0.0 | 0 | 2 |
| hate-typal-beast | hate-typal-beast | hate-tribal-beast | 0 | 0.0 | 0 | 4 |
| hate-typal-bird | hate-typal-bird |  | 0 | 0.0 | 0 | 2 |
| hate-typal-choose | hate-typal-choose | hate-tribal-choose | 0 | 0.0 | 0 | 18 |
| hate-typal-cleric | hate-typal-cleric | hate-tribal-cleric | 0 | 0.0 | 0 | 8 |
| hate-typal-coward | hate-typal-coward | hate-tribal-coward | 0 | 0.0 | 0 | 5 |
| hate-typal-coyote | hate-typal-coyote |  | 0 | 0.0 | 0 | 1 |
| hate-typal-cyclops | hate-typal-cyclops | hate-tribal-cyclops | 0 | 0.0 | 0 | 1 |
| hate-typal-dalek | hate-typal-dalek |  | 0 | 0.0 | 0 | 2 |
| hate-typal-demon | hate-typal-demon | hate-tribal-demon | 0 | 0.0 | 0 | 4 |
| hate-typal-devil | hate-typal-devil | hate-tribal-devil | 0 | 0.0 | 0 | 1 |
| hate-typal-dinosaur | hate-typal-dinosaur | hate-tribal-dinosaur | 0 | 0.0 | 0 | 2 |
| hate-typal-djinn | hate-typal-djinn | hate-tribal-djinn | 0 | 0.0 | 0 | 2 |
| hate-typal-dog | hate-typal-dog | hate-tribal-dog | 0 | 0.0 | 0 | 1 |
| hate-typal-dragon | hate-typal-dragon | hate-tribal-dragon;hate-dragon | 0 | 0.0 | 0 | 8 |
| hate-typal-efreet | hate-typal-efreet | hate-tribal-efreet | 0 | 0.0 | 0 | 2 |
| hate-typal-eldrazi | hate-typal-eldrazi | hate-tribal-eldrazi | 0 | 0.0 | 0 | 2 |
| hate-typal-eldrazi-scion | hate-typal-eldrazi-scion | hate-tribal-eldrazi-scion | 0 | 0.0 | 0 | 1 |
| hate-typal-elf | hate-typal-elf | hate-tribal-elf | 0 | 0.0 | 0 | 11 |
| hate-typal-elk | hate-typal-elk |  | 0 | 0.0 | 0 | 1 |
| hate-typal-giant | hate-typal-giant | hate-tribal-giant | 0 | 0.0 | 0 | 1 |
| hate-typal-glimmer | hate-typal-glimmer |  | 0 | 0.0 | 0 | 1 |
| hate-typal-god | hate-typal-god | hate-tribal-god | 0 | 0.0 | 0 | 4 |
| hate-typal-gorgon | hate-typal-gorgon | hate-tribal-gorgon | 0 | 0.0 | 0 | 1 |
| hate-typal-homarid | hate-typal-homarid | hate-tribal-homarid | 0 | 0.0 | 0 | 1 |
| hate-typal-inkling | hate-typal-inkling | hate-tribal-inkling | 0 | 0.0 | 0 | 1 |
| hate-typal-kavu | hate-typal-kavu | hate-tribal-kavu | 0 | 0.0 | 0 | 3 |
| hate-typal-kithkin | hate-typal-kithkin | hate-tribal-kithkin | 0 | 0.0 | 0 | 1 |
| hate-typal-knight | hate-typal-knight | hate-tribal-knight | 0 | 0.0 | 0 | 2 |
| hate-typal-lizard | hate-typal-lizard |  | 0 | 0.0 | 0 | 1 |
| hate-typal-mercenary | hate-typal-mercenary | hate-tribal-mercenary | 0 | 0.0 | 0 | 3 |
| hate-typal-mutant | hate-typal-mutant | hate-tribal-mutant | 0 | 0.0 | 0 | 2 |
| hate-typal-ninja | hate-typal-ninja | hate-tribal-ninja | 0 | 0.0 | 0 | 1 |
| hate-typal-non-choose | hate-typal-non-choose | hate-tribal-non-choose | 0 | 0.0 | 0 | 6 |
| hate-typal-non-dragon | hate-typal-non-dragon | hate-tribal-non-dragon | 0 | 0.0 | 0 | 8 |
| hate-typal-non-elf | hate-typal-non-elf | hate-tribal-non-elf | 0 | 0.0 | 0 | 7 |
| hate-typal-non-god | hate-typal-non-god |  | 0 | 0.0 | 0 | 1 |
| hate-typal-non-human | hate-typal-non-human | hate-tribal-non-human | 0 | 0.0 | 0 | 6 |
| hate-typal-non-spirit | hate-typal-non-spirit | hate-tribal-non-spirit | 0 | 0.0 | 0 | 7 |
| hate-typal-non-wall | hate-typal-non-wall | hate-tribal-non-wall | 0 | 0.0 | 0 | 20 |
| hate-typal-non-zombie | hate-typal-non-zombie | hate-tribal-non-zombie | 0 | 0.0 | 0 | 6 |
| hate-typal-orc | hate-typal-orc | hate-tribal-orc | 0 | 0.0 | 0 | 4 |
| hate-typal-ox | hate-typal-ox |  | 0 | 0.0 | 0 | 2 |
| hate-typal-phyrexian | hate-typal-phyrexian |  | 0 | 0.0 | 0 | 1 |
| hate-typal-pirate | hate-typal-pirate |  | 0 | 0.0 | 0 | 1 |
| hate-typal-rat | hate-typal-rat | hate-tribal-rat | 0 | 0.0 | 0 | 2 |
| hate-typal-rebel | hate-typal-rebel | hate-tribal-rebel | 0 | 0.0 | 0 | 2 |
| hate-typal-reflection | hate-typal-reflection | hate-tribal-reflection | 0 | 0.0 | 0 | 2 |
| hate-typal-robot | hate-typal-robot |  | 0 | 0.0 | 0 | 3 |
| hate-typal-rogue | hate-typal-rogue | hate-tribal-rogue | 0 | 0.0 | 0 | 2 |
| hate-typal-salamander | hate-typal-salamander | hate-tribal-salamander | 0 | 0.0 | 0 | 1 |
| hate-typal-saproling | hate-typal-saproling | hate-tribal-saproling | 0 | 0.0 | 0 | 1 |
| hate-typal-scarecrow | hate-typal-scarecrow | hate-tribal-scarecrow | 0 | 0.0 | 0 | 1 |
| hate-typal-serf | hate-typal-serf | hate-tribal-serf | 0 | 0.0 | 0 | 1 |
| hate-typal-share | hate-typal-share | hate-tribal-share | 0 | 0.0 | 0 | 4 |
| hate-typal-skeleton | hate-typal-skeleton | hate-tribal-skeleton | 0 | 0.0 | 0 | 3 |
| hate-typal-sliver | hate-typal-sliver | hate-tribal-sliver | 0 | 0.0 | 0 | 4 |
| hate-typal-soldier | hate-typal-soldier |  | 0 | 0.0 | 0 | 1 |
| hate-typal-spider | hate-typal-spider |  | 0 | 0.0 | 0 | 1 |
| hate-typal-spirit | hate-typal-spirit | hate-spirit;hate-tribal-spirit | 0 | 0.0 | 0 | 16 |
| hate-typal-survivor | hate-typal-survivor | hate-tribal-survivor | 0 | 0.0 | 0 | 1 |
| hate-typal-thrull | hate-typal-thrull | hate-tribal-thrull | 0 | 0.0 | 0 | 1 |
| hate-typal-treefolk | hate-typal-treefolk | hate-tribal-treefolk | 0 | 0.0 | 0 | 2 |
| hate-typal-villain | hate-typal-villain |  | 0 | 0.0 | 0 | 1 |
| hate-typal-warlock | hate-typal-warlock |  | 0 | 0.0 | 0 | 1 |
| hate-typal-warrior | hate-typal-warrior |  | 0 | 0.0 | 0 | 1 |
| hate-typal-werewolf | hate-typal-werewolf | hate-tribal-werewolf | 0 | 0.0 | 0 | 6 |
| hate-typal-wizard | hate-typal-wizard | hate-tribal-wizard | 0 | 0.0 | 0 | 5 |
| hate-typal-wolf | hate-typal-wolf | hate-tribal-wolf | 0 | 0.0 | 0 | 1 |
| hate-typal-yeti | hate-typal-yeti |  | 0 | 0.0 | 0 | 1 |
| hate-untapped | hate-untapped |  | 0 | 0.0 | 0 | 2 |
| hate-vehicle | hate-vehicle |  | 0 | 0.0 | 0 | 28 |
| hate-vigilance | hate-vigilance |  | 0 | 0.0 | 0 | 2 |
| hate-ward | hate-ward |  | 0 | 0.0 | 0 | 1 |
| hate-warp | hate-warp |  | 0 | 0.0 | 0 | 1 |
| hatebird | hatebird |  | 0 | 0.0 | 0 | 19 |
| hats-matter | hats matter |  | 0 | 0.0 | 0 | 9 |
| heckbent | heckbent |  | 0 | 0.0 | 0 | 11 |
| hellbent | hellbent |  | 0 | 0.0 | 0 | 54 |
| helper-card | helper card | assistant cards;assistant card | 0 | 0.0 | 0 | 33 |
| hexproof-counter | hexproof counter |  | 0 | 0.0 | 0 | 8 |
| hexproof-soft | hexproof soft |  | 0 | 0.0 | 0 | 22 |
| high-five-matters | high five matters |  | 0 | 0.0 | 0 | 3 |
| hunger-reanimation | hunger reanimation |  | 0 | 0.0 | 0 | 6 |
| hungry-demon | hungry demon |  | 0 | 0.0 | 0 | 37 |
| imprinted-card-types-matter | imprinted card types matter |  | 0 | 0.0 | 0 | 10 |
| improvise | improvise |  | 0 | 0.0 | 0 | 24 |
| impulse-artifact-creature | impulse-artifact-creature |  | 0 | 0.0 | 0 | 2 |
| impulse-artifact-equipment | impulse-artifact-equipment |  | 0 | 0.0 | 0 | 10 |
| impulse-artifact-legendary | impulse-artifact-legendary |  | 0 | 0.0 | 0 | 1 |
| impulse-artifact-spacecraft | impulse-artifact-spacecraft |  | 0 | 0.0 | 0 | 1 |
| impulse-artifact-vehicle | impulse-artifact-vehicle |  | 0 | 0.0 | 0 | 6 |
| impulse-battle | impulse-battle |  | 0 | 0.0 | 0 | 5 |
| impulse-black | impulse-black |  | 0 | 0.0 | 0 | 1 |
| impulse-blue | impulse-blue |  | 0 | 0.0 | 0 | 1 |
| impulse-cast | impulse-cast |  | 0 | 0.0 | 0 | 29 |
| impulse-color | impulse-color |  | 0 | 0.0 | 0 | 7 |
| impulse-colorless | impulse-colorless |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-ally | impulse-creature-ally |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-angel | impulse-creature-angel |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-assassin | impulse-creature-assassin |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-demon | impulse-creature-demon |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-dinosaur | impulse-creature-dinosaur |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-dragon | impulse-creature-dragon |  | 0 | 0.0 | 0 | 5 |
| impulse-creature-dwarf | impulse-creature-dwarf |  | 0 | 0.0 | 0 | 3 |
| impulse-creature-elemental | impulse-creature-elemental |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-elf | impulse-creature-elf |  | 0 | 0.0 | 0 | 4 |
| impulse-creature-goblin | impulse-creature-goblin |  | 0 | 0.0 | 0 | 3 |
| impulse-creature-hero | impulse-creature-hero |  | 0 | 0.0 | 0 | 4 |
| impulse-creature-human | impulse-creature-human |  | 0 | 0.0 | 0 | 4 |
| impulse-creature-kavu | impulse-creature-kavu |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-knight | impulse-creature-knight |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-legendary | impulse-creature-legendary |  | 0 | 0.0 | 0 | 2 |
| impulse-creature-merfolk | impulse-creature-merfolk |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-mutant | impulse-creature-mutant |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-ninja | impulse-creature-ninja |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-pirate | impulse-creature-pirate |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-rat | impulse-creature-rat |  | 0 | 0.0 | 0 | 1 |
| impulse-creature-soldier | impulse-creature-soldier |  | 0 | 0.0 | 0 | 2 |
| impulse-creature-turtle | impulse-creature-turtle |  | 0 | 0.0 | 0 | 2 |
| impulse-creature-warrior | impulse-creature-warrior |  | 0 | 0.0 | 0 | 2 |
| impulse-creature-zombie | impulse-creature-zombie |  | 0 | 0.0 | 0 | 1 |
| impulse-enchantment | impulse-enchantment |  | 0 | 0.0 | 0 | 38 |
| impulse-enchantment-aura | impulse-enchantment-aura |  | 0 | 0.0 | 0 | 7 |
| impulse-enchantment-saga | impulse-enchantment-saga |  | 0 | 0.0 | 0 | 6 |
| impulse-enchantment-shrine | impulse-enchantment-shrine |  | 0 | 0.0 | 0 | 1 |
| impulse-green | impulse-green |  | 0 | 0.0 | 0 | 2 |
| impulse-historic | impulse-historic |  | 0 | 0.0 | 0 | 3 |
| impulse-instant | impulse-instant |  | 0 | 0.0 | 0 | 24 |
| impulse-instant-sorcery-lesson | impulse-instant-sorcery-lesson |  | 0 | 0.0 | 0 | 2 |
| impulse-legendary | impulse-legendary |  | 0 | 0.0 | 0 | 8 |
| impulse-multicolor | impulse-multicolor |  | 0 | 0.0 | 0 | 1 |
| impulse-noncreature | impulse-noncreature |  | 0 | 0.0 | 0 | 8 |
| impulse-nonland | impulse-nonland |  | 0 | 0.0 | 0 | 7 |
| impulse-planeswalker | impulse-planeswalker |  | 0 | 0.0 | 0 | 17 |
| impulse-pw-garruk | impulse-pw-garruk |  | 0 | 0.0 | 0 | 1 |
| impulse-pw-tyvar | impulse-pw-tyvar |  | 0 | 0.0 | 0 | 1 |
| impulse-red | impulse-red |  | 0 | 0.0 | 0 | 1 |
| impulse-sorcery | impulse-sorcery |  | 0 | 0.0 | 0 | 24 |
| impulse-white | impulse-white |  | 0 | 0.0 | 0 | 1 |
| impulsive-curiosity | impulsive curiosity |  | 0 | 0.0 | 0 | 21 |
| impulsive-freecast | impulsive freecast |  | 0 | 0.0 | 0 | 19 |
| impulsive-recursion | impulsive recursion |  | 0 | 0.0 | 0 | 21 |
| indestructible-counter | indestructible counter |  | 0 | 0.0 | 0 | 27 |
| infernal-spawn-family | infernal spawn family |  | 0 | 0.0 | 0 | 3 |
| ingest | ingest |  | 0 | 0.0 | 0 | 36 |
| inspired | inspired |  | 0 | 0.0 | 0 | 34 |
| instant-loyalty-ability | instant loyalty ability |  | 0 | 0.0 | 0 | 6 |
| ip-matters | ip matters |  | 0 | 0.0 | 0 | 3 |
| islandfall | islandfall |  | 0 | 0.0 | 0 | 5 |
| jackal-pup-ability | jackal pup ability |  | 0 | 0.0 | 0 | 9 |
| just-shuffle | just shuffle |  | 0 | 0.0 | 0 | 20 |
| karnstructs | karnstructs |  | 0 | 0.0 | 0 | 8 |
| keyword-counter | keyword counter | ability counter | 0 | 0.0 | 0 | 138 |
| keyword-errata-hexproof | keyword errata hexproof |  | 0 | 0.0 | 0 | 3 |
| keyword-errata-surveil | keyword errata surveil |  | 0 | 0.0 | 0 | 17 |
| keyword-soup | keyword soup |  | 0 | 0.0 | 0 | 27 |
| keywords-matter | keywords matter |  | 0 | 0.0 | 0 | 7 |
| kismet-effect | kismet effect |  | 0 | 0.0 | 0 | 29 |
| klingon | klingon |  | 0 | 0.0 | 0 | 1 |
| krarks-other-thumb-effect | krarks other thumb effect |  | 0 | 0.0 | 0 | 8 |
| land-kavu | land kavu |  | 0 | 0.0 | 0 | 3 |
| landhome | landhome |  | 0 | 0.0 | 0 | 35 |
| landslow | landslow |  | 0 | 0.0 | 0 | 12 |
| last-chance | last chance |  | 0 | 0.0 | 0 | 6 |
| leaves-graveyard-trigger | leaves graveyard trigger |  | 0 | 0.0 | 0 | 51 |
| leaving-graveyard-matters | leaving graveyard matters |  | 0 | 0.0 | 0 | 59 |
| legacy | legacy |  | 0 | 0.0 | 0 | 28 |
| legendary-team-up | legendary team-up |  | 0 | 0.0 | 0 | 49 |
| legendfall | legendfall |  | 0 | 0.0 | 0 | 19 |
| legendify | legendify |  | 0 | 0.0 | 0 | 61 |
| legends-retold | legends retold |  | 0 | 0.0 | 0 | 20 |
| leyline | leyline |  | 0 | 0.0 | 0 | 19 |
| library-size-matters | library size matters |  | 0 | 0.0 | 0 | 23 |
| lich-effect | lich effect |  | 0 | 0.0 | 0 | 14 |
| life-divider | life divider | lose half life | 0 | 0.0 | 0 | 40 |
| life-divider-opponent | life divider-opponent |  | 0 | 0.0 | 0 | 31 |
| life-divider-you | life divider-you |  | 0 | 0.0 | 0 | 22 |
| life-doubler | life doubler |  | 0 | 0.0 | 0 | 6 |
| lifelink-counter | lifelink counter |  | 0 | 0.0 | 0 | 27 |
| lightning-bolt-redux | lightning bolt redux |  | 0 | 0.0 | 0 | 18 |
| liliana's-pact-demon | liliana's pact demon |  | 0 | 0.0 | 0 | 4 |
| lobotomy | lobotomy |  | 0 | 0.0 | 0 | 36 |
| location-matters | location matters |  | 0 | 0.0 | 0 | 2 |
| lockdown-artifact | lockdown-artifact |  | 0 | 0.0 | 0 | 16 |
| lockdown-land | lockdown-land |  | 0 | 0.0 | 0 | 10 |
| lockdown-nonland | lockdown-nonland |  | 0 | 0.0 | 0 | 2 |
| lockdown-permanent | lockdown-permanent |  | 0 | 0.0 | 0 | 4 |
| lockdown-planeswalker | lockdown-planeswalker |  | 0 | 0.0 | 0 | 2 |
| lockdown-spacecraft | lockdown-spacecraft |  | 0 | 0.0 | 0 | 1 |
| loner | loner |  | 0 | 0.0 | 0 | 13 |
| loot-to-exile | loot to exile |  | 0 | 0.0 | 0 | 7 |
| loot-to-library | loot to library |  | 0 | 0.0 | 0 | 10 |
| lose-trigger | lose trigger |  | 0 | 0.0 | 0 | 12 |
| lose-unspent-mana | lose unspent mana |  | 0 | 0.0 | 0 | 5 |
| low-x-matters | low x matters |  | 0 | 0.0 | 0 | 3 |
| madness | madness |  | 0 | 0.0 | 0 | 63 |
| magecraft | magecraft |  | 0 | 0.0 | 0 | 32 |
| mana-abilities-matter | mana abilities matter |  | 0 | 0.0 | 0 | 13 |
| mana-egg | mana egg | manarock-egg | 0 | 0.0 | 0 | 42 |
| mana-source-(type) | mana source (type) |  | 0 | 0.0 | 0 | 2 |
| manaless-land | manaless land |  | 0 | 0.0 | 0 | 19 |
| maro | maro |  | 0 | 0.0 | 0 | 38 |
| marvel-storyline-name | marvel storyline name |  | 0 | 0.0 | 0 | 4 |
| mass-reanimation | mass reanimation |  | 0 | 0.0 | 0 | 76 |
| match-points-matter | match points matter |  | 0 | 0.0 | 0 | 1 |
| mechanical-foreshadow | mechanical foreshadow |  | 0 | 0.0 | 0 | 13 |
| menace-counter | menace counter |  | 0 | 0.0 | 0 | 16 |
| mimic | mimic |  | 0 | 0.0 | 0 | 37 |
| miniwheel | miniwheel |  | 0 | 0.0 | 0 | 48 |
| mirror-gallery | mirror gallery |  | 0 | 0.0 | 0 | 10 |
| misnomer | misnomer |  | 0 | 0.0 | 0 | 97 |
| mixed-subtypes | mixed subtypes |  | 0 | 0.0 | 0 | 92 |
| mob-name | mob name |  | 0 | 0.0 | 0 | 10 |
| monarch-matters | monarch matters |  | 0 | 0.0 | 0 | 49 |
| mono-red-value | mono-red value |  | 0 | 0.0 | 0 | 1 |
| monstrosity | monstrosity |  | 0 | 0.0 | 0 | 36 |
| morphling | morphling |  | 0 | 0.0 | 0 | 10 |
| mountainfall | mountainfall |  | 0 | 0.0 | 0 | 7 |
| move-counters | move counters | counter movement | 0 | 0.0 | 0 | 67 |
| moxen | moxen | manarock-mox | 0 | 0.0 | 0 | 15 |
| multiclass-party-member | multiclass party member |  | 0 | 0.0 | 0 | 4 |
| multicolor-kicker | multicolor kicker |  | 0 | 0.0 | 0 | 19 |
| multiple-kicker-costs | multiple kicker costs |  | 0 | 0.0 | 0 | 18 |
| mutiny | mutiny |  | 0 | 0.0 | 0 | 9 |
| named-choice | named choice |  | 0 | 0.0 | 0 | 61 |
| named-token | named token |  | 0 | 0.0 | 0 | 87 |
| nanni | nanni |  | 0 | 0.0 | 0 | 1 |
| nemesis-mega-cycle | nemesis-mega-cycle |  | 0 | 0.0 | 0 | 3 |
| nevermore | nevermore | meddling mage;comply | 0 | 0.0 | 0 | 11 |
| night-matters | night matters |  | 0 | 0.0 | 0 | 3 |
| nimble | nimble |  | 0 | 0.0 | 0 | 9 |
| ninjutsu | ninjutsu |  | 0 | 0.0 | 0 | 37 |
| no-mercy | no mercy |  | 0 | 0.0 | 0 | 8 |
| no-creature-type | no-creature-type |  | 0 | 0.0 | 0 | 9 |
| no-planeswalker-type | no-planeswalker-type |  | 0 | 0.0 | 0 | 5 |
| non-integer | non-integer |  | 0 | 0.0 | 0 | 30 |
| noncreature-virtual-vanilla | noncreature virtual vanilla |  | 0 | 0.0 | 0 | 3 |
| nonfunctional-reminder-counter | nonfunctional reminder counter |  | 0 | 0.0 | 0 | 13 |
| nonstandard-bestow | nonstandard-bestow |  | 0 | 0.0 | 0 | 5 |
| noted-tracked-information | noted tracked information |  | 0 | 0.0 | 0 | 20 |
| null-rod | null rod |  | 0 | 0.0 | 0 | 6 |
| o-ring-with-set-mechanic | o-ring with set mechanic | banish with set mechanic | 0 | 0.0 | 0 | 28 |
| off-turn-attack | off-turn attack |  | 0 | 0.0 | 0 | 2 |
| offspring-token | offspring token |  | 0 | 0.0 | 0 | 20 |
| oil-counters-matter | oil counters matter |  | 0 | 0.0 | 0 | 44 |
| old-damage-deathtouch | old damage deathtouch |  | 0 | 0.0 | 0 | 23 |
| old-fight | old fight |  | 0 | 0.0 | 0 | 10 |
| old-lifelink | old lifelink |  | 0 | 0.0 | 0 | 28 |
| old-mana-burn-clause | old mana burn clause |  | 0 | 0.0 | 0 | 4 |
| old-typeline | old typeline |  | 0 | 0.0 | 0 | 5 |
| old-ward | old ward |  | 0 | 0.0 | 0 | 7 |
| omnivore-ability | omnivore ability |  | 0 | 0.0 | 0 | 11 |
| one-off | one-off |  | 0 | 0.0 | 0 | 6 |
| opaline-effect | opaline effect |  | 0 | 0.0 | 0 | 18 |
| open-attraction | open attraction |  | 0 | 0.0 | 0 | 46 |
| opponent-sacrifice-matters | opponent sacrifice matters | their sacrifice matters;synergy-opponent-sacrifice | 0 | 0.0 | 0 | 19 |
| other-games-matter | other games matter |  | 0 | 0.0 | 0 | 19 |
| outlast-mentor | outlast mentor |  | 0 | 0.0 | 0 | 7 |
| outnumber | outnumber |  | 0 | 0.0 | 0 | 25 |
| outside-objects-matter | outside objects matter |  | 0 | 0.0 | 0 | 5 |
| ownership-change-in-hand | ownership change in hand |  | 0 | 0.0 | 0 | 2 |
| painland | painland |  | 0 | 0.0 | 0 | 52 |
| paper-compatible | paper-compatible |  | 0 | 0.0 | 0 | 185 |
| parasitic-aura | parasitic aura | pseudo-curse | 0 | 0.0 | 0 | 56 |
| pariah | pariah |  | 0 | 0.0 | 0 | 22 |
| passive-ability | passive ability |  | 0 | 0.0 | 0 | 106 |
| peek-face-down | peek-face-down | face-down peek | 0 | 0.0 | 0 | 9 |
| permanentfall | permanentfall |  | 0 | 0.0 | 0 | 32 |
| persecution-effect | persecution effect |  | 0 | 0.0 | 0 | 8 |
| persist | persist |  | 0 | 0.0 | 0 | 26 |
| phasing | phasing |  | 0 | 0.0 | 0 | 75 |
| phasing-matters | phasing matters |  | 0 | 0.0 | 0 | 8 |
| phoenix-with-set's-mechanic | phoenix with set's mechanic | phoenix with sets mechanic;phoenix with set mechanic | 0 | 0.0 | 0 | 15 |
| phyrexian-mana | phyrexian mana |  | 0 | 0.0 | 0 | 77 |
| phyrexian-mana-ability | phyrexian mana ability |  | 0 | 0.0 | 0 | 37 |
| phyrexian-mana-cost | phyrexian mana cost |  | 0 | 0.0 | 0 | 41 |
| phyrexian-token | phyrexian token |  | 0 | 0.0 | 0 | 11 |
| pierce | pierce |  | 0 | 0.0 | 0 | 7 |
| pile | pile |  | 0 | 0.0 | 0 | 13 |
| pile-card | pile card |  | 0 | 0.0 | 0 | 9 |
| place-sticker | place sticker |  | 0 | 0.0 | 0 | 58 |
| plainsfall | plainsfall |  | 0 | 0.0 | 0 | 3 |
| planechase-mechanic | planechase mechanic |  | 0 | 0.0 | 0 | 14 |
| planeswalker-deck-face-card | planeswalker deck face card |  | 0 | 0.0 | 0 | 41 |
| planeswalker-deck-staples | planeswalker deck staples |  | 0 | 0.0 | 0 | 74 |
| planeswalkerfall | planeswalkerfall |  | 0 | 0.0 | 0 | 3 |
| platinum-angel-effect | platinum angel effect |  | 0 | 0.0 | 0 | 12 |
| player-spotlight | player spotlight |  | 0 | 0.0 | 0 | 5 |
| players-outside-game-matter | players outside game matter |  | 0 | 0.0 | 0 | 36 |
| playtest-forecast | playtest forecast |  | 0 | 0.0 | 0 | 30 |
| polymorph | polymorph |  | 0 | 0.0 | 0 | 41 |
| potentially-black-border | potentially black border | non-acorn silver border | 0 | 0.0 | 0 | 522 |
| power-nine | power nine |  | 0 | 0.0 | 0 | 9 |
| powerstone-mana | powerstone mana |  | 0 | 0.0 | 0 | 47 |
| pre-game-choice | pre-game choice |  | 0 | 0.0 | 0 | 9 |
| predefined-token | predefined token |  | 0 | 0.0 | 0 | 20 |
| preexisting-dnd-background | preexisting dnd background |  | 0 | 0.0 | 0 | 20 |
| prevent-cast | prevent cast | prevents casting | 0 | 0.0 | 0 | 94 |
| prevent-damage-redirection | prevent damage redirection |  | 0 | 0.0 | 0 | 4 |
| prevent-etb | prevent etb |  | 0 | 0.0 | 0 | 9 |
| prevent-extra-turns | prevent extra turns | hate-extra-turn | 0 | 0.0 | 0 | 4 |
| prevent-mass-blockers | prevent mass blockers | prevent blocker-mass | 0 | 0.0 | 0 | 55 |
| prevent-put-counter | prevent put counter |  | 0 | 0.0 | 0 | 11 |
| prevent-sacrifice | prevent sacrifice |  | 0 | 0.0 | 0 | 17 |
| prevent-trigger | prevent trigger |  | 0 | 0.0 | 0 | 8 |
| prevent-transform | prevent-transform |  | 0 | 0.0 | 0 | 2 |
| prevents-win/loss | prevents win/loss | prevents win;prevents loss | 0 | 0.0 | 0 | 35 |
| probe | probe |  | 0 | 0.0 | 0 | 7 |
| processing | processing |  | 0 | 0.0 | 0 | 26 |
| promotes-to-commander | promotes to commander |  | 0 | 0.0 | 0 | 7 |
| protects-nonland | protects-nonland |  | 0 | 0.0 | 0 | 7 |
| protects-token | protects-token |  | 0 | 0.0 | 0 | 2 |
| proto-finality | proto-finality |  | 0 | 0.0 | 0 | 15 |
| prowess-anthem | prowess anthem |  | 0 | 0.0 | 0 | 8 |
| pseudo-ante | pseudo-ante |  | 0 | 0.0 | 0 | 1 |
| pseudo-cycling | pseudo-cycling |  | 0 | 0.0 | 0 | 11 |
| pseudo-dethrone | pseudo-dethrone | dethrone effect | 0 | 0.0 | 0 | 12 |
| pseudo-equipment | pseudo-equipment | old equipment templating | 0 | 0.0 | 0 | 13 |
| pseudo-haste | pseudo-haste |  | 0 | 0.0 | 0 | 6 |
| pseudo-intimidate | pseudo-intimidate |  | 0 | 0.0 | 0 | 4 |
| pseudo-legendary | pseudo-legendary |  | 0 | 0.0 | 0 | 2 |
| pseudo-leveler | pseudo-leveler | figure of destiny | 0 | 0.0 | 0 | 10 |
| pseudo-proliferate | pseudo-proliferate | virtual proliferate | 0 | 0.0 | 0 | 51 |
| punchcard | punchcard |  | 0 | 0.0 | 0 | 2 |
| purgatory | purgatory | death haven | 0 | 0.0 | 0 | 8 |
| pwdeck-sidekick | pwdeck-sidekick |  | 0 | 0.0 | 0 | 38 |
| pwdeck-tutor | pwdeck-tutor |  | 0 | 0.0 | 0 | 36 |
| quadratic | quadratic |  | 0 | 0.0 | 0 | 80 |
| quick-enchant | quick enchant |  | 0 | 0.0 | 0 | 23 |
| quietus-effect | quietus effect |  | 0 | 0.0 | 0 | 12 |
| quote-name | quote name |  | 0 | 0.0 | 0 | 50 |
| radiate | radiate |  | 0 | 0.0 | 0 | 19 |
| rampage | rampage |  | 0 | 0.0 | 0 | 26 |
| random-card | random card | momir | 0 | 0.0 | 0 | 49 |
| ransom | ransom | hostage | 0 | 0.0 | 0 | 36 |
| rarity-matters | rarity matters |  | 0 | 0.0 | 0 | 8 |
| reach-counter | reach counter |  | 0 | 0.0 | 0 | 14 |
| reanimate-artifact-creature | reanimate-artifact-creature |  | 0 | 0.0 | 0 | 8 |
| reanimate-aura | reanimate-aura |  | 0 | 0.0 | 0 | 21 |
| reanimate-battle | reanimate-battle |  | 0 | 0.0 | 0 | 2 |
| reanimate-cast | reanimate-cast |  | 0 | 0.0 | 0 | 153 |
| reanimate-enchantment | reanimate-enchantment |  | 0 | 0.0 | 0 | 34 |
| reanimate-equipment | reanimate-equipment |  | 0 | 0.0 | 0 | 15 |
| reanimate-face-down | reanimate-face-down |  | 0 | 0.0 | 0 | 9 |
| reanimate-historic | reanimate-historic |  | 0 | 0.0 | 0 | 2 |
| reanimate-instant/sorcery | reanimate-instant/sorcery | reanimate-instant;reanimate-sorcery | 0 | 0.0 | 0 | 1 |
| reanimate-legendary | reanimate-legendary |  | 0 | 0.0 | 0 | 3 |
| reanimate-noncreature | reanimate-noncreature |  | 0 | 0.0 | 0 | 3 |
| reanimate-nonland | reanimate-nonland |  | 0 | 0.0 | 0 | 25 |
| reanimate-permanent | reanimate-permanent |  | 0 | 0.0 | 0 | 64 |
| reanimate-planeswalker | reanimate-planeswalker |  | 0 | 0.0 | 0 | 20 |
| reanimate-saga | reanimate-saga |  | 0 | 0.0 | 0 | 3 |
| reanimate-spacecraft | reanimate-spacecraft |  | 0 | 0.0 | 0 | 2 |
| reanimate-vehicle | reanimate-vehicle |  | 0 | 0.0 | 0 | 9 |
| recasting-commander-matters | recasting commander matters |  | 0 | 0.0 | 0 | 20 |
| recurring-suspend | recurring suspend |  | 0 | 0.0 | 0 | 11 |
| recursion-battle | recursion-battle |  | 0 | 0.0 | 0 | 7 |
| recursion-planeswalker | recursion-planeswalker |  | 0 | 0.0 | 0 | 85 |
| regrowth-arcane | regrowth-arcane |  | 0 | 0.0 | 0 | 1 |
| regrowth-artifact | regrowth-artifact |  | 0 | 0.0 | 0 | 76 |
| regrowth-artifact-creature | regrowth-artifact-creature |  | 0 | 0.0 | 0 | 2 |
| regrowth-aura | regrowth-aura |  | 0 | 0.0 | 0 | 6 |
| regrowth-battle | regrowth-battle |  | 0 | 0.0 | 0 | 3 |
| regrowth-equipment | regrowth-equipment |  | 0 | 0.0 | 0 | 7 |
| regrowth-food | regrowth-food |  | 0 | 0.0 | 0 | 1 |
| regrowth-historic | regrowth-historic |  | 0 | 0.0 | 0 | 5 |
| regrowth-legendary | regrowth-legendary |  | 0 | 0.0 | 0 | 8 |
| regrowth-noncreature | regrowth-noncreature |  | 0 | 0.0 | 0 | 3 |
| regrowth-nonland | regrowth-nonland |  | 0 | 0.0 | 0 | 5 |
| regrowth-nonland-permanent | regrowth-nonland-permanent |  | 0 | 0.0 | 0 | 2 |
| regrowth-planeswalker | regrowth-planeswalker |  | 0 | 0.0 | 0 | 65 |
| regrowth-saga | regrowth-saga |  | 0 | 0.0 | 0 | 5 |
| regrowth-spacecraft | regrowth-spacecraft |  | 0 | 0.0 | 0 | 2 |
| regrowth-vehicle | regrowth-vehicle |  | 0 | 0.0 | 0 | 4 |
| relentless | relentless | singleton-breaker | 0 | 0.0 | 0 | 14 |
| reminder-card | reminder card |  | 0 | 0.0 | 0 | 10 |
| reminder-text-matters | reminder text matters |  | 0 | 0.0 | 0 | 3 |
| removal-nonenchantment | removal-nonenchantment |  | 0 | 0.0 | 0 | 3 |
| removal-token | removal-token |  | 0 | 0.0 | 0 | 4 |
| remove-counters-other | remove counters-other |  | 0 | 0.0 | 0 | 48 |
| remove-counters-player | remove counters-player |  | 0 | 0.0 | 0 | 131 |
| remove-from-combat | remove from combat |  | 0 | 0.0 | 0 | 26 |
| remove-from-stack | remove-from-stack |  | 0 | 0.0 | 0 | 45 |
| removes-banding | removes banding |  | 0 | 0.0 | 0 | 2 |
| removes-deathtouch | removes deathtouch |  | 0 | 0.0 | 0 | 1 |
| removes-defender | removes defender |  | 0 | 0.0 | 0 | 14 |
| removes-double-strike | removes double strike |  | 0 | 0.0 | 0 | 1 |
| removes-first-strike | removes first strike |  | 0 | 0.0 | 0 | 6 |
| removes-flying | removes flying |  | 0 | 0.0 | 0 | 36 |
| removes-hexproof | removes hexproof | hate-hexproof | 0 | 0.0 | 0 | 11 |
| removes-indestructible | removes indestructible | hate-indestructible | 0 | 0.0 | 0 | 12 |
| removes-infect | removes infect |  | 0 | 0.0 | 0 | 1 |
| removes-landwalk | removes landwalk |  | 0 | 0.0 | 0 | 4 |
| removes-protection | removes protection |  | 0 | 0.0 | 0 | 2 |
| removes-shadow | removes shadow |  | 0 | 0.0 | 0 | 2 |
| removes-shroud | removes shroud | hate-shroud | 0 | 0.0 | 0 | 2 |
| removes-toxic | removes toxic |  | 0 | 0.0 | 0 | 1 |
| removes-trample | removes trample | hate-trample | 0 | 0.0 | 0 | 4 |
| removes-ward | removes ward |  | 0 | 0.0 | 0 | 1 |
| renown | renown |  | 0 | 0.0 | 0 | 20 |
| repeatable-blood | repeatable blood |  | 0 | 0.0 | 0 | 19 |
| repeatable-clues | repeatable clues |  | 0 | 0.0 | 0 | 91 |
| repeatable-enchantment-tokens | repeatable enchantment tokens |  | 0 | 0.0 | 0 | 28 |
| repeatable-gold | repeatable gold |  | 0 | 0.0 | 0 | 4 |
| repeatable-junk | repeatable junk |  | 0 | 0.0 | 0 | 7 |
| repeatable-land-tokens | repeatable land tokens |  | 0 | 0.0 | 0 | 6 |
| repeatable-landers | repeatable landers |  | 0 | 0.0 | 0 | 3 |
| repeatable-maps | repeatable maps |  | 0 | 0.0 | 0 | 6 |
| repeatable-mulch | repeatable mulch |  | 0 | 0.0 | 0 | 57 |
| repeatable-mutagens | repeatable mutagens |  | 0 | 0.0 | 0 | 8 |
| repeatable-powerstones | repeatable powerstones |  | 0 | 0.0 | 0 | 13 |
| repeatable-roles | repeatable roles |  | 0 | 0.0 | 0 | 5 |
| repeatable-seek | repeatable seek |  | 0 | 0.0 | 0 | 43 |
| repeatable-vibranium | repeatable vibranium |  | 0 | 0.0 | 0 | 3 |
| rescue-aura | rescue-aura |  | 0 | 0.0 | 0 | 3 |
| rescue-nonartifact | rescue-nonartifact |  | 0 | 0.0 | 0 | 1 |
| restart-game | restart game |  | 0 | 0.0 | 0 | 2 |
| restart-turn | restart turn |  | 0 | 0.0 | 0 | 1 |
| restock-any | restock-any |  | 0 | 0.0 | 0 | 27 |
| restock-battle | restock-battle |  | 0 | 0.0 | 0 | 2 |
| restock-enchantment | restock-enchantment |  | 0 | 0.0 | 0 | 2 |
| restock-instant | restock-instant |  | 0 | 0.0 | 0 | 10 |
| restock-land | restock-land |  | 0 | 0.0 | 0 | 3 |
| restock-noncreature | restock-noncreature |  | 0 | 0.0 | 0 | 1 |
| restock-nonland | restock-nonland |  | 0 | 0.0 | 0 | 1 |
| restock-permanent | restock-permanent |  | 0 | 0.0 | 0 | 1 |
| restock-sorcery | restock-sorcery |  | 0 | 0.0 | 0 | 10 |
| restock-to-bottom | restock-to-bottom |  | 0 | 0.0 | 0 | 48 |
| restores-old-rule | restores old rule |  | 0 | 0.0 | 0 | 8 |
| retaliate-to-damage | retaliate to damage | retaliate damage | 0 | 0.0 | 0 | 45 |
| revolt | revolt | disappear | 0 | 0.0 | 0 | 35 |
| ritual-untap | ritual-untap |  | 0 | 0.0 | 0 | 20 |
| roll-d10 | roll d10 |  | 0 | 0.0 | 0 | 3 |
| roll-d12 | roll d12 |  | 0 | 0.0 | 0 | 3 |
| roll-d20 | roll d20 |  | 0 | 0.0 | 0 | 55 |
| roll-d4 | roll d4 |  | 0 | 0.0 | 0 | 5 |
| roll-d6 | roll d6 |  | 0 | 0.0 | 0 | 129 |
| roll-d8 | roll d8 |  | 0 | 0.0 | 0 | 4 |
| roll-planar-die | roll planar die |  | 0 | 0.0 | 0 | 1 |
| roll-to-visit | roll to visit |  | 0 | 0.0 | 0 | 2 |
| roman-numeral | roman numeral |  | 0 | 0.0 | 0 | 14 |
| royal-assassin-ability | royal assassin ability |  | 0 | 0.0 | 0 | 8 |
| rule-of-law | rule of law |  | 0 | 0.0 | 0 | 13 |
| rulebreaker | rulebreaker | relaxed commander restriction | 0 | 0.0 | 0 | 22 |
| rules-nightmare | rules nightmare |  | 0 | 0.0 | 0 | 48 |
| rules-text-matters | rules text matters |  | 0 | 0.0 | 0 | 17 |
| rummage-to-library | rummage to library |  | 0 | 0.0 | 0 | 10 |
| sacrifice-cost-land | sacrifice cost land |  | 0 | 0.0 | 0 | 9 |
| sacrifice-outlet-nonland | sacrifice outlet-nonland | sac outlet-nonland | 0 | 0.0 | 0 | 20 |
| sacrifice-outlet-token | sacrifice outlet-token | sac outlet-token | 0 | 0.0 | 0 | 46 |
| save-from-death | save from death |  | 0 | 0.0 | 0 | 7 |
| scene | scene |  | 0 | 0.0 | 0 | 24 |
| scooch-dice | scooch dice |  | 0 | 0.0 | 0 | 4 |
| scry-like | scry like |  | 0 | 0.0 | 0 | 48 |
| second-spell-matters | second spell matters | flurry | 0 | 0.0 | 0 | 70 |
| secretly-choose | secretly choose |  | 0 | 0.0 | 0 | 31 |
| seek | seek | tutor-seek | 0 | 0.0 | 0 | 113 |
| seek-artifact | seek-artifact |  | 0 | 0.0 | 0 | 6 |
| seek-artifact-spacecraft | seek-artifact-spacecraft |  | 0 | 0.0 | 0 | 1 |
| seek-card | seek-card |  | 0 | 0.0 | 0 | 17 |
| seek-cast | seek-cast |  | 0 | 0.0 | 0 | 1 |
| seek-creature | seek-creature |  | 0 | 0.0 | 0 | 32 |
| seek-creature-dragon | seek-creature-dragon |  | 0 | 0.0 | 0 | 2 |
| seek-creature-elf | seek-creature-elf |  | 0 | 0.0 | 0 | 2 |
| seek-creature-kithkin | seek-creature-kithkin |  | 0 | 0.0 | 0 | 1 |
| seek-creature-merfolk | seek-creature-merfolk |  | 0 | 0.0 | 0 | 1 |
| seek-creature-pirate | seek-creature-pirate |  | 0 | 0.0 | 0 | 1 |
| seek-creature-rat | seek-creature-rat |  | 0 | 0.0 | 0 | 1 |
| seek-creature-survivor | seek-creature-survivor |  | 0 | 0.0 | 0 | 1 |
| seek-creature-vampire | seek-creature-vampire |  | 0 | 0.0 | 0 | 1 |
| seek-enchantment | seek-enchantment |  | 0 | 0.0 | 0 | 2 |
| seek-enchantment-saga | seek-enchantment-saga |  | 0 | 0.0 | 0 | 1 |
| seek-instant | seek-instant |  | 0 | 0.0 | 0 | 6 |
| seek-land | seek-land |  | 0 | 0.0 | 0 | 19 |
| seek-land-any | seek-land-any |  | 0 | 0.0 | 0 | 12 |
| seek-land-basic | seek-land-basic |  | 0 | 0.0 | 0 | 2 |
| seek-land-forest | seek-land-forest |  | 0 | 0.0 | 0 | 3 |
| seek-land-island | seek-land-island |  | 0 | 0.0 | 0 | 1 |
| seek-land-mountain | seek-land-mountain |  | 0 | 0.0 | 0 | 2 |
| seek-land-nonbasic | seek-land-nonbasic |  | 0 | 0.0 | 0 | 1 |
| seek-land-plains | seek-land-plains |  | 0 | 0.0 | 0 | 1 |
| seek-land-swamp | seek-land-swamp |  | 0 | 0.0 | 0 | 1 |
| seek-land-urza's | seek-land-urza's |  | 0 | 0.0 | 0 | 1 |
| seek-legendary | seek-legendary |  | 0 | 0.0 | 0 | 1 |
| seek-mv | seek-mv |  | 0 | 0.0 | 0 | 38 |
| seek-noncreature | seek-noncreature |  | 0 | 0.0 | 0 | 1 |
| seek-nonland | seek-nonland |  | 0 | 0.0 | 0 | 35 |
| seek-permanent | seek-permanent |  | 0 | 0.0 | 0 | 6 |
| seek-planeswalker | seek-planeswalker |  | 0 | 0.0 | 0 | 2 |
| seek-self | seek-self |  | 0 | 0.0 | 0 | 1 |
| seek-sorcery | seek-sorcery |  | 0 | 0.0 | 0 | 6 |
| seek-to-battlefield | seek-to-battlefield |  | 0 | 0.0 | 0 | 24 |
| seek-to-exile | seek-to-exile |  | 0 | 0.0 | 0 | 4 |
| seek-to-graveyard | seek-to-graveyard |  | 0 | 0.0 | 0 | 3 |
| seek-to-hand | seek-to-hand |  | 0 | 0.0 | 0 | 87 |
| seek-to-zone | seek-to-zone |  | 0 | 0.0 | 0 | 112 |
| set-matters | set matters |  | 0 | 0.0 | 0 | 22 |
| shadow-counter | shadow counter |  | 0 | 0.0 | 0 | 3 |
| shapesharing | shapesharing |  | 0 | 0.0 | 0 | 101 |
| share-counters | share counters |  | 0 | 0.0 | 0 | 10 |
| shares-name-with-a-format | shares name with a format |  | 0 | 0.0 | 0 | 7 |
| shares-name-with-a-set | shares name with a set |  | 0 | 0.0 | 0 | 32 |
| shockland | shockland |  | 0 | 0.0 | 0 | 11 |
| show-and-tell | show and tell |  | 0 | 0.0 | 0 | 9 |
| shroud-from-black | shroud from black |  | 0 | 0.0 | 0 | 1 |
| shroud-from-blue | shroud from blue |  | 0 | 0.0 | 0 | 1 |
| shroud-from-nongreen | shroud from nongreen |  | 0 | 0.0 | 0 | 1 |
| shroud-from-red | shroud from red |  | 0 | 0.0 | 0 | 1 |
| shroud-from-white | shroud from white |  | 0 | 0.0 | 0 | 2 |
| sideboard-matters | sideboard matters |  | 0 | 0.0 | 0 | 6 |
| siege-(modal) | siege (modal) | siege | 0 | 0.0 | 0 | 15 |
| silence | silence |  | 0 | 0.0 | 0 | 38 |
| single-minded-typal-hate | single-minded typal hate |  | 0 | 0.0 | 0 | 14 |
| singleton-matters | singleton matters |  | 0 | 0.0 | 0 | 3 |
| skip-draw-step | skip draw step |  | 0 | 0.0 | 0 | 20 |
| skip-turn | skip turn |  | 0 | 0.0 | 0 | 14 |
| skip-untap-step | skip untap step |  | 0 | 0.0 | 0 | 11 |
| skulk | skulk |  | 0 | 0.0 | 0 | 18 |
| sleeping-enchantment | sleeping enchantment |  | 0 | 0.0 | 0 | 29 |
| sleeves-matter | sleeves matter |  | 0 | 0.0 | 0 | 5 |
| sliver-stackable | sliver-stackable |  | 0 | 0.0 | 0 | 46 |
| sneak-from-command-zone | sneak from command zone |  | 0 | 0.0 | 0 | 7 |
| sneak-artifact | sneak-artifact |  | 0 | 0.0 | 0 | 22 |
| sneak-artifact-creature | sneak-artifact-creature |  | 0 | 0.0 | 0 | 1 |
| sneak-aura | sneak-aura |  | 0 | 0.0 | 0 | 10 |
| sneak-enchantment | sneak-enchantment |  | 0 | 0.0 | 0 | 3 |
| sneak-equipment | sneak-equipment |  | 0 | 0.0 | 0 | 5 |
| sneak-permanent | sneak-permanent | sneak-permanent-any | 0 | 0.0 | 0 | 33 |
| sneak-planeswalker | sneak-planeswalker |  | 0 | 0.0 | 0 | 5 |
| snowfall | snowfall |  | 0 | 0.0 | 0 | 3 |
| sol-land | sol land |  | 0 | 0.0 | 0 | 12 |
| special-action | special action |  | 0 | 0.0 | 0 | 25 |
| specialized | specialized |  | 0 | 0.0 | 0 | 95 |
| specific-power-matters | specific power matters |  | 0 | 0.0 | 0 | 23 |
| specific-toughness-matters | specific toughness matters |  | 0 | 0.0 | 0 | 17 |
| speech-matters | speech matters |  | 0 | 0.0 | 0 | 61 |
| speed-matters | speed matters |  | 0 | 0.0 | 0 | 11 |
| spell-with-no-casting-cost | spell with no casting cost |  | 0 | 0.0 | 0 | 20 |
| splits-on-death | splits on death |  | 0 | 0.0 | 0 | 64 |
| squad-token | squad token |  | 0 | 0.0 | 0 | 6 |
| square-stats-matter | square stats matter |  | 0 | 0.0 | 0 | 4 |
| star-trek-episode-saga | star trek episode saga |  | 0 | 0.0 | 0 | 14 |
| start-of-game | start of game | opening card | 0 | 0.0 | 0 | 55 |
| starting-player-matters | starting player matters | rule of go | 0 | 0.0 | 0 | 18 |
| stasis | stasis |  | 0 | 0.0 | 0 | 38 |
| static-from-graveyard | static-from-graveyard |  | 0 | 0.0 | 0 | 1 |
| sth-storyline-in-cards | sth-storyline-in-cards |  | 0 | 0.0 | 0 | 34 |
| stock-turn | stock turn |  | 0 | 0.0 | 0 | 3 |
| storage-land | storage land |  | 0 | 0.0 | 0 | 20 |
| storm-count-matters | storm count matters |  | 0 | 0.0 | 0 | 28 |
| storm-like | storm-like |  | 0 | 0.0 | 0 | 22 |
| stronger-in-singleton-formats | stronger in singleton formats |  | 0 | 0.0 | 0 | 6 |
| stun-counters-matter | stun counters matter |  | 0 | 0.0 | 0 | 3 |
| substance | substance |  | 0 | 0.0 | 0 | 12 |
| substitute-card | substitute card |  | 0 | 0.0 | 0 | 10 |
| sunburst | sunburst |  | 0 | 0.0 | 0 | 28 |
| super-menace | super-menace |  | 0 | 0.0 | 0 | 13 |
| supercycle-legendary-land | supercycle-legendary-land |  | 0 | 0.0 | 0 | 5 |
| support | support |  | 0 | 0.0 | 0 | 66 |
| surge | surge |  | 0 | 0.0 | 0 | 28 |
| swampfall | swampfall |  | 0 | 0.0 | 0 | 6 |
| sword-of-x-and-y | sword of x and y | sword of a and b | 0 | 0.0 | 0 | 14 |
| synergy-full-hand | synergy full hand |  | 0 | 0.0 | 0 | 11 |
| synergy-1/1 | synergy-1/1 |  | 0 | 0.0 | 0 | 10 |
| synergy-ability-sticker | synergy-ability-sticker |  | 0 | 0.0 | 0 | 3 |
| synergy-activated-ability | synergy-activated-ability |  | 0 | 0.0 | 0 | 67 |
| synergy-adventure | synergy-adventure |  | 0 | 0.0 | 0 | 18 |
| synergy-affinity | synergy-affinity |  | 0 | 0.0 | 0 | 1 |
| synergy-airbending | synergy-airbending |  | 0 | 0.0 | 0 | 1 |
| synergy-art-sticker | synergy-art-sticker |  | 0 | 0.0 | 0 | 10 |
| synergy-attraction | synergy-attraction |  | 0 | 0.0 | 0 | 14 |
| synergy-augment | synergy-augment |  | 0 | 0.0 | 0 | 8 |
| synergy-awaken | synergy-awaken |  | 0 | 0.0 | 0 | 1 |
| synergy-backup | synergy-backup |  | 0 | 0.0 | 0 | 2 |
| synergy-banana | synergy-banana |  | 0 | 0.0 | 0 | 1 |
| synergy-banding | synergy-banding |  | 0 | 0.0 | 0 | 5 |
| synergy-bargain | synergy-bargain |  | 0 | 0.0 | 0 | 1 |
| synergy-battle | synergy-battle |  | 0 | 0.0 | 0 | 36 |
| synergy-blitz | synergy-blitz |  | 0 | 0.0 | 0 | 1 |
| synergy-blood | synergy-blood |  | 0 | 0.0 | 0 | 18 |
| synergy-boast | synergy-boast |  | 0 | 0.0 | 0 | 3 |
| synergy-bobblehead | synergy-bobblehead |  | 0 | 0.0 | 0 | 7 |
| synergy-boon | synergy-boon |  | 0 | 0.0 | 0 | 1 |
| synergy-bushido | synergy-bushido |  | 0 | 0.0 | 0 | 1 |
| synergy-cascade | synergy-cascade |  | 0 | 0.0 | 0 | 3 |
| synergy-case | synergy-case |  | 0 | 0.0 | 0 | 1 |
| synergy-cave | synergy-cave |  | 0 | 0.0 | 0 | 13 |
| synergy-changeling | synergy-changeling |  | 0 | 0.0 | 0 | 1 |
| synergy-chorus | synergy-chorus |  | 0 | 0.0 | 0 | 5 |
| synergy-clash | synergy-clash |  | 0 | 0.0 | 0 | 4 |
| synergy-class | synergy-class |  | 0 | 0.0 | 0 | 1 |
| synergy-clue | synergy-clue |  | 0 | 0.0 | 0 | 34 |
| synergy-collect-evidence | synergy-collect evidence |  | 0 | 0.0 | 0 | 3 |
| synergy-color-non-share | synergy-color-non-share |  | 0 | 0.0 | 0 | 1 |
| synergy-colored | synergy-colored |  | 0 | 0.0 | 0 | 7 |
| synergy-colorless | synergy-colorless | colourless matters | 0 | 0.0 | 0 | 63 |
| synergy-colorless-mana | synergy-colorless-mana |  | 0 | 0.0 | 0 | 3 |
| synergy-communicator | synergy-communicator |  | 0 | 0.0 | 0 | 2 |
| synergy-conjure | synergy-conjure |  | 0 | 0.0 | 0 | 4 |
| synergy-connive | synergy-connive |  | 0 | 0.0 | 0 | 4 |
| synergy-contraption | synergy-contraption |  | 0 | 0.0 | 0 | 6 |
| synergy-convoke | synergy-convoke |  | 0 | 0.0 | 0 | 3 |
| synergy-copy | synergy-copy |  | 0 | 0.0 | 0 | 38 |
| synergy-counterspell | synergy-counterspell |  | 0 | 0.0 | 0 | 5 |
| synergy-craft | synergy-craft |  | 0 | 0.0 | 0 | 1 |
| synergy-creatureland | synergy-creatureland | lord-creatureland | 0 | 0.0 | 0 | 21 |
| synergy-cumulative-upkeep | synergy-cumulative upkeep |  | 0 | 0.0 | 0 | 2 |
| synergy-curse | synergy-curse |  | 0 | 0.0 | 0 | 5 |
| synergy-cycling | synergy-cycling |  | 0 | 0.0 | 0 | 48 |
| synergy-damage-prevention | synergy-damage-prevention |  | 0 | 0.0 | 0 | 1 |
| synergy-dash | synergy-dash |  | 0 | 0.0 | 0 | 1 |
| synergy-desert | synergy-desert |  | 0 | 0.0 | 0 | 31 |
| synergy-devoid | synergy-devoid |  | 0 | 0.0 | 0 | 2 |
| synergy-devour | synergy-devour |  | 0 | 0.0 | 0 | 1 |
| synergy-dfc | synergy-dfc |  | 0 | 0.0 | 0 | 5 |
| synergy-dice | synergy-dice |  | 0 | 0.0 | 0 | 50 |
| synergy-dimension | synergy-dimension |  | 0 | 0.0 | 0 | 1 |
| synergy-discover | synergy-discover |  | 0 | 0.0 | 0 | 2 |
| synergy-disguise | synergy-disguise |  | 0 | 0.0 | 0 | 1 |
| synergy-disturb | synergy-disturb |  | 0 | 0.0 | 0 | 3 |
| synergy-doctor's-companion | synergy-doctor's companion |  | 0 | 0.0 | 0 | 2 |
| synergy-double-strike | synergy-double-strike |  | 0 | 0.0 | 0 | 24 |
| synergy-dungeon | synergy-dungeon |  | 0 | 0.0 | 0 | 24 |
| synergy-earthbending | synergy-earthbending |  | 0 | 0.0 | 0 | 1 |
| synergy-echo | synergy-echo |  | 0 | 0.0 | 0 | 1 |
| synergy-embalm | synergy-embalm |  | 0 | 0.0 | 0 | 1 |
| synergy-emblem | synergy-emblem |  | 0 | 0.0 | 0 | 2 |
| synergy-enchantment-creature | synergy-enchantment-creature |  | 0 | 0.0 | 0 | 22 |
| synergy-energy | synergy-energy |  | 0 | 0.0 | 0 | 2 |
| synergy-enlist | synergy-enlist |  | 0 | 0.0 | 0 | 1 |
| synergy-equipment-legendary | synergy-equipment-legendary |  | 0 | 0.0 | 0 | 1 |
| synergy-eternalize | synergy-eternalize |  | 0 | 0.0 | 0 | 1 |
| synergy-exert | synergy-exert |  | 0 | 0.0 | 0 | 5 |
| synergy-exhaust | synergy-exhaust |  | 0 | 0.0 | 0 | 8 |
| synergy-exiling | synergy-exiling |  | 0 | 0.0 | 0 | 25 |
| synergy-exploit | synergy-exploit |  | 0 | 0.0 | 0 | 3 |
| synergy-explore | synergy-explore |  | 0 | 0.0 | 0 | 8 |
| synergy-face-down | synergy-face-down |  | 0 | 0.0 | 0 | 29 |
| synergy-face-down-cast | synergy-face-down-cast |  | 0 | 0.0 | 0 | 7 |
| synergy-fear | synergy-fear |  | 0 | 0.0 | 0 | 4 |
| synergy-fight | synergy-fight |  | 0 | 0.0 | 0 | 4 |
| synergy-firebending | synergy-firebending |  | 0 | 0.0 | 0 | 1 |
| synergy-first-strike | synergy-first-strike |  | 0 | 0.0 | 0 | 26 |
| synergy-flanking | synergy-flanking |  | 0 | 0.0 | 0 | 3 |
| synergy-food | synergy-food |  | 0 | 0.0 | 0 | 93 |
| synergy-forage | synergy-forage |  | 0 | 0.0 | 0 | 2 |
| synergy-foretell | synergy-foretell |  | 0 | 0.0 | 0 | 7 |
| synergy-freerunning | synergy-freerunning |  | 0 | 0.0 | 0 | 2 |
| synergy-gift | synergy-gift |  | 0 | 0.0 | 0 | 1 |
| synergy-goad | synergy-goad |  | 0 | 0.0 | 0 | 9 |
| synergy-haste | synergy-haste |  | 0 | 0.0 | 0 | 52 |
| synergy-haunt | synergy-haunt |  | 0 | 0.0 | 0 | 1 |
| synergy-hexproof | synergy-hexproof |  | 0 | 0.0 | 0 | 18 |
| synergy-historic | synergy-historic |  | 0 | 0.0 | 0 | 68 |
| synergy-horsemanship | synergy-horsemanship |  | 0 | 0.0 | 0 | 2 |
| synergy-hybrid | synergy-hybrid |  | 0 | 0.0 | 0 | 2 |
| synergy-incubator | synergy-incubator |  | 0 | 0.0 | 0 | 10 |
| synergy-indestructible | synergy-indestructible |  | 0 | 0.0 | 0 | 20 |
| synergy-ingest | synergy-ingest |  | 0 | 0.0 | 0 | 1 |
| synergy-initiative | synergy-initiative |  | 0 | 0.0 | 0 | 9 |
| synergy-intimidate | synergy-intimidate |  | 0 | 0.0 | 0 | 1 |
| synergy-investigate | synergy-investigate |  | 0 | 0.0 | 0 | 2 |
| synergy-jump-start | synergy-jump-start |  | 0 | 0.0 | 0 | 1 |
| synergy-junk | synergy-junk |  | 0 | 0.0 | 0 | 2 |
| synergy-land-graveyard | synergy-land-graveyard |  | 0 | 0.0 | 0 | 12 |
| synergy-lander | synergy-lander |  | 0 | 0.0 | 0 | 2 |
| synergy-landwalk | synergy-landwalk |  | 0 | 0.0 | 0 | 5 |
| synergy-leaves-creature | synergy-leaves-creature |  | 0 | 0.0 | 0 | 3 |
| synergy-legendary | synergy-legendary |  | 0 | 0.0 | 0 | 295 |
| synergy-lesson | synergy-lesson |  | 0 | 0.0 | 0 | 29 |
| synergy-level-up | synergy-level-up |  | 0 | 0.0 | 0 | 3 |
| synergy-life-payment | synergy-life-payment |  | 0 | 0.0 | 0 | 2 |
| synergy-lifelink | synergy-lifelink |  | 0 | 0.0 | 0 | 22 |
| synergy-locus | synergy-locus |  | 0 | 0.0 | 0 | 7 |
| synergy-madness | synergy-madness |  | 0 | 0.0 | 0 | 1 |
| synergy-manifest | synergy-manifest |  | 0 | 0.0 | 0 | 2 |
| synergy-manifest-dread | synergy-manifest-dread |  | 0 | 0.0 | 0 | 2 |
| synergy-map | synergy-map |  | 0 | 0.0 | 0 | 1 |
| synergy-menace | synergy-menace |  | 0 | 0.0 | 0 | 24 |
| synergy-mentor | synergy-mentor |  | 0 | 0.0 | 0 | 1 |
| synergy-modal | synergy-modal |  | 0 | 0.0 | 0 | 13 |
| synergy-modified | synergy-modified |  | 0 | 0.0 | 0 | 48 |
| synergy-modular | synergy-modular |  | 0 | 0.0 | 0 | 2 |
| synergy-monocolor | synergy-monocolor |  | 0 | 0.0 | 0 | 6 |
| synergy-morph | synergy-morph |  | 0 | 0.0 | 0 | 2 |
| synergy-multicolor-pair | synergy-multicolor-pair |  | 0 | 0.0 | 0 | 7 |
| synergy-multicolor-trio | synergy-multicolor-trio |  | 0 | 0.0 | 0 | 2 |
| synergy-mutate | synergy-mutate |  | 0 | 0.0 | 0 | 7 |
| synergy-name-sticker | synergy-name-sticker |  | 0 | 0.0 | 0 | 22 |
| synergy-ninjutsu | synergy-ninjutsu |  | 0 | 0.0 | 0 | 3 |
| synergy-no-flying | synergy-no-flying |  | 0 | 0.0 | 0 | 18 |
| synergy-nonbasic-land | synergy-nonbasic-land |  | 0 | 0.0 | 0 | 6 |
| synergy-omen | synergy-omen |  | 0 | 0.0 | 0 | 4 |
| synergy-p/t-sticker | synergy-p/t-sticker |  | 0 | 0.0 | 0 | 2 |
| synergy-partner | synergy-partner |  | 0 | 0.0 | 0 | 1 |
| synergy-party | synergy-party | typal-party;tribal-party | 0 | 0.0 | 0 | 49 |
| synergy-pin | synergy-pin |  | 0 | 0.0 | 0 | 2 |
| synergy-plan | synergy-plan |  | 0 | 0.0 | 0 | 2 |
| synergy-planet | synergy-planet |  | 0 | 0.0 | 0 | 5 |
| synergy-playtest | synergy-playtest |  | 0 | 0.0 | 0 | 7 |
| synergy-plot | synergy-plot |  | 0 | 0.0 | 0 | 1 |
| synergy-poison | synergy-poison |  | 0 | 0.0 | 0 | 42 |
| synergy-power-up | synergy-power-up |  | 0 | 0.0 | 0 | 5 |
| synergy-powerstone | synergy-powerstone |  | 0 | 0.0 | 0 | 2 |
| synergy-proliferate | synergy-proliferate |  | 0 | 0.0 | 0 | 7 |
| synergy-protection | synergy-protection |  | 0 | 0.0 | 0 | 9 |
| synergy-pw-ajani | synergy-pw-ajani | typal-ajani | 0 | 0.0 | 0 | 2 |
| synergy-pw-angrath | synergy-pw-angrath | typal-angrath | 0 | 0.0 | 0 | 1 |
| synergy-pw-ashiok | synergy-pw-ashiok | typal-ashiok | 0 | 0.0 | 0 | 1 |
| synergy-pw-basri | synergy-pw-basri | typal-basri | 0 | 0.0 | 0 | 1 |
| synergy-pw-bolas | synergy-pw-bolas | typal-bolas | 0 | 0.0 | 0 | 5 |
| synergy-pw-chandra | synergy-pw-chandra | typal-chandra | 0 | 0.0 | 0 | 7 |
| synergy-pw-choose | synergy-pw-choose | typal-pw-choose | 0 | 0.0 | 0 | 2 |
| synergy-pw-davriel | synergy-pw-davriel | typal-davriel | 0 | 0.0 | 0 | 1 |
| synergy-pw-domri | synergy-pw-domri | typal-domri | 0 | 0.0 | 0 | 1 |
| synergy-pw-dovin | synergy-pw-dovin | typal-dovin | 0 | 0.0 | 0 | 1 |
| synergy-pw-elspeth | synergy-pw-elspeth | typal-elspeth | 0 | 0.0 | 0 | 1 |
| synergy-pw-garruk | synergy-pw-garruk | typal-garruk | 0 | 0.0 | 0 | 4 |
| synergy-pw-gideon | synergy-pw-gideon | typal-gideon | 0 | 0.0 | 0 | 5 |
| synergy-pw-huatli | synergy-pw-huatli | typal-huatli | 0 | 0.0 | 0 | 1 |
| synergy-pw-liliana | synergy-pw-liliana | typal-liliana | 0 | 0.0 | 0 | 5 |
| synergy-pw-lukka | synergy-pw-lukka | typal-lukka | 0 | 0.0 | 0 | 1 |
| synergy-pw-nissa | synergy-pw-nissa | typal-nissa | 0 | 0.0 | 0 | 3 |
| synergy-pw-oko | synergy-pw-oko | typal-oko | 0 | 0.0 | 0 | 1 |
| synergy-pw-ral | synergy-pw-ral | typal-ral | 0 | 0.0 | 0 | 1 |
| synergy-pw-rowan | synergy-pw-rowan | typal-rowan | 0 | 0.0 | 0 | 1 |
| synergy-pw-sarkhan | synergy-pw-sarkhan | typal-sarkhan | 0 | 0.0 | 0 | 1 |
| synergy-pw-tamiyo | synergy-pw-tamiyo | typal-tamiyo | 0 | 0.0 | 0 | 1 |
| synergy-pw-teferi | synergy-pw-teferi | typal-teferi | 0 | 0.0 | 0 | 2 |
| synergy-pw-tezzeret | synergy-pw-tezzeret | typal-tezzeret | 0 | 0.0 | 0 | 2 |
| synergy-pw-tyvar | synergy-pw-tyvar | typal-tyvar | 0 | 0.0 | 0 | 2 |
| synergy-pw-ugin | synergy-pw-ugin | typal-ugin | 0 | 0.0 | 0 | 1 |
| synergy-pw-vivien | synergy-pw-vivien | typal-vivien | 0 | 0.0 | 0 | 2 |
| synergy-pw-vraska | synergy-pw-vraska | typal-vraska | 0 | 0.0 | 0 | 2 |
| synergy-pw-yanggu | synergy-pw-yanggu | typal-yanggu | 0 | 0.0 | 0 | 1 |
| synergy-pw-yanling | synergy-pw-yanling | typal-yanling | 0 | 0.0 | 0 | 2 |
| synergy-reach | synergy-reach |  | 0 | 0.0 | 0 | 21 |
| synergy-regenerate | synergy-regenerate |  | 0 | 0.0 | 0 | 1 |
| synergy-renown | synergy-renown |  | 0 | 0.0 | 0 | 3 |
| synergy-ring | synergy-ring |  | 0 | 0.0 | 0 | 13 |
| synergy-role | synergy-role |  | 0 | 0.0 | 0 | 1 |
| synergy-room | synergy-room |  | 0 | 0.0 | 0 | 26 |
| synergy-rune | synergy-rune |  | 0 | 0.0 | 0 | 2 |
| synergy-saddle | synergy-saddle |  | 0 | 0.0 | 0 | 1 |
| synergy-saga | synergy-saga |  | 0 | 0.0 | 0 | 88 |
| synergy-seek | synergy-seek |  | 0 | 0.0 | 0 | 3 |
| synergy-self-burn | synergy-self-burn |  | 0 | 0.0 | 0 | 4 |
| synergy-shadow | synergy-shadow |  | 0 | 0.0 | 0 | 6 |
| synergy-shrine | synergy-shrine |  | 0 | 0.0 | 0 | 28 |
| synergy-shroud | synergy-shroud |  | 0 | 0.0 | 0 | 3 |
| synergy-skulk | synergy-skulk |  | 0 | 0.0 | 0 | 2 |
| synergy-sneak | synergy-sneak |  | 0 | 0.0 | 0 | 1 |
| synergy-snow | synergy-snow |  | 0 | 0.0 | 0 | 61 |
| synergy-soulbond | synergy-soulbond |  | 0 | 0.0 | 0 | 2 |
| synergy-spacecraft | synergy-spacecraft |  | 0 | 0.0 | 0 | 30 |
| synergy-spectacle | synergy-spectacle |  | 0 | 0.0 | 0 | 1 |
| synergy-sphere | synergy-sphere |  | 0 | 0.0 | 0 | 3 |
| synergy-start-your-engines | synergy-start-your-engines |  | 0 | 0.0 | 0 | 1 |
| synergy-sticker | synergy-sticker | stickers matter | 0 | 0.0 | 0 | 79 |
| synergy-suspect | synergy-suspect |  | 0 | 0.0 | 0 | 10 |
| synergy-suspend | synergy-suspend |  | 0 | 0.0 | 0 | 25 |
| synergy-tantrum | synergy-tantrum |  | 0 | 0.0 | 0 | 1 |
| synergy-teamwork | synergy-teamwork |  | 0 | 0.0 | 0 | 2 |
| synergy-theft | synergy-theft |  | 0 | 0.0 | 0 | 29 |
| synergy-town | synergy-town |  | 0 | 0.0 | 0 | 7 |
| synergy-toxic | synergy-toxic |  | 0 | 0.0 | 0 | 10 |
| synergy-transform | synergy-transform |  | 0 | 0.0 | 0 | 16 |
| synergy-treasure | synergy-treasure |  | 0 | 0.0 | 0 | 53 |
| synergy-tuck | synergy-tuck |  | 0 | 0.0 | 0 | 2 |
| synergy-tutor | synergy-tutor |  | 0 | 0.0 | 0 | 5 |
| synergy-type-change | synergy-type-change |  | 0 | 0.0 | 0 | 1 |
| synergy-unearth | synergy-unearth |  | 0 | 0.0 | 0 | 3 |
| synergy-untapped | synergy-untapped |  | 0 | 0.0 | 0 | 10 |
| synergy-urza's | synergy-urza's |  | 0 | 0.0 | 0 | 1 |
| synergy-vanilla | synergy-vanilla |  | 0 | 0.0 | 0 | 6 |
| synergy-vehicle | synergy-vehicle |  | 0 | 0.0 | 0 | 135 |
| synergy-vigilance | synergy-vigilance |  | 0 | 0.0 | 0 | 28 |
| synergy-villainous-choice | synergy-villainous-choice |  | 0 | 0.0 | 0 | 1 |
| synergy-vote | synergy-vote |  | 0 | 0.0 | 0 | 8 |
| synergy-warp | synergy-warp |  | 0 | 0.0 | 0 | 22 |
| synergy-wastes | synergy-wastes |  | 0 | 0.0 | 0 | 2 |
| synergy-waterbending | synergy-waterbending |  | 0 | 0.0 | 0 | 1 |
| synergy-wither | synergy-wither |  | 0 | 0.0 | 0 | 1 |
| table-order-matters | table order matters |  | 0 | 0.0 | 0 | 21 |
| take-the-initiative | take the initiative | take-initiative | 0 | 0.0 | 0 | 23 |
| tap-fuel-artifact | tap fuel-artifact |  | 0 | 0.0 | 0 | 99 |
| tap-fuel-land | tap fuel-land |  | 0 | 0.0 | 0 | 25 |
| tap-fuel-permanent | tap fuel-permanent |  | 0 | 0.0 | 0 | 5 |
| tap-fuel-token | tap fuel-token |  | 0 | 0.0 | 0 | 6 |
| tappable-enchantment | tappable enchantment |  | 0 | 0.0 | 0 | 4 |
| tapped-matters-self | tapped matters-self |  | 0 | 0.0 | 0 | 29 |
| tapper-nonland | tapper-nonland |  | 0 | 0.0 | 0 | 18 |
| tapper-permanent | tapper-permanent | tap permanent | 0 | 0.0 | 0 | 51 |
| tapper-planeswalker | tapper-planeswalker |  | 0 | 0.0 | 0 | 5 |
| tapper-spacecraft | tapper-spacecraft |  | 0 | 0.0 | 0 | 1 |
| tax-block | tax block |  | 0 | 0.0 | 0 | 7 |
| team-matters | team matters |  | 0 | 0.0 | 0 | 19 |
| tearing | tearing |  | 0 | 0.0 | 0 | 2 |
| temporary-counter | temporary counter |  | 0 | 0.0 | 0 | 4 |
| text-change-color | text change color |  | 0 | 0.0 | 0 | 10 |
| that's-how-the-game-works | that's how the game works |  | 0 | 0.0 | 0 | 16 |
| the-doctor | the doctor |  | 0 | 0.0 | 0 | 17 |
| the-ring-tempts-you | the ring tempts you |  | 0 | 0.0 | 0 | 49 |
| theft-artifact-creature | theft-artifact-creature |  | 0 | 0.0 | 0 | 1 |
| theft-aura | theft-aura |  | 0 | 0.0 | 0 | 3 |
| theft-commander | theft-commander |  | 0 | 0.0 | 0 | 1 |
| theft-enchantment | theft-enchantment |  | 0 | 0.0 | 0 | 9 |
| theft-equipment | theft-equipment |  | 0 | 0.0 | 0 | 7 |
| theft-land | theft-land |  | 0 | 0.0 | 0 | 26 |
| theft-legendary | theft-legendary |  | 0 | 0.0 | 0 | 1 |
| theft-mana | theft-mana |  | 0 | 0.0 | 0 | 3 |
| theft-mass | theft-mass |  | 0 | 0.0 | 0 | 51 |
| theft-nonland | theft-nonland |  | 0 | 0.0 | 0 | 24 |
| theft-ownership | theft-ownership |  | 0 | 0.0 | 0 | 15 |
| theft-planeswalker | theft-planeswalker |  | 0 | 0.0 | 0 | 13 |
| theft-saga | theft-saga |  | 0 | 0.0 | 0 | 1 |
| theft-spacecraft | theft-spacecraft |  | 0 | 0.0 | 0 | 1 |
| theft-spell | theft-spell |  | 0 | 0.0 | 0 | 14 |
| third-draw-matters | third draw matters |  | 0 | 0.0 | 0 | 8 |
| third-spell-matters | third spell matters |  | 0 | 0.0 | 0 | 3 |
| time-matters | time matters |  | 0 | 0.0 | 0 | 9 |
| timing-restriction | timing restriction |  | 0 | 0.0 | 0 | 52 |
| token-doubler | token doubler |  | 0 | 0.0 | 0 | 19 |
| token-increaser | token increaser |  | 0 | 0.0 | 0 | 34 |
| token-replacer | token replacer |  | 0 | 0.0 | 0 | 11 |
| token-version-of-a-card | token version of a card |  | 0 | 0.0 | 0 | 43 |
| token-without-a-card | token without a card |  | 0 | 0.0 | 0 | 15 |
| tokenfall | tokenfall |  | 0 | 0.0 | 0 | 20 |
| tokenlink | tokenlink | bloodsower effect | 0 | 0.0 | 0 | 31 |
| toughness-matters-self | toughness matters-self |  | 0 | 0.0 | 0 | 21 |
| toughness-matters-total | toughness matters-total |  | 0 | 0.0 | 0 | 7 |
| toys-matter | toys matter |  | 0 | 0.0 | 0 | 3 |
| trading-post-like | trading post like |  | 0 | 0.0 | 0 | 17 |
| trample-counter | trample counter |  | 0 | 0.0 | 0 | 22 |
| transcendental-life/damage | transcendental life/damage |  | 0 | 0.0 | 0 | 2 |
| transform-improvement | transform-improvement |  | 0 | 0.0 | 0 | 54 |
| transform-mirror | transform-mirror |  | 0 | 0.0 | 0 | 9 |
| tribal-whale | tribal-whale |  | 0 | 0.0 | 0 | 1 |
| tribute | tribute |  | 0 | 0.0 | 0 | 11 |
| tricycle-land | tricycle-land |  | 0 | 0.0 | 0 | 10 |
| trigger-from-exile | trigger from exile |  | 0 | 0.0 | 0 | 83 |
| trigger-once-each-turn | trigger-once-each-turn |  | 0 | 0.0 | 0 | 1 |
| triggers-at-cleanup-step | triggers at cleanup step |  | 0 | 0.0 | 0 | 14 |
| triome | triome |  | 0 | 0.0 | 0 | 10 |
| tuck-outlet | tuck-outlet |  | 0 | 0.0 | 0 | 44 |
| turn-face-down | turn-face-down |  | 0 | 0.0 | 0 | 10 |
| turn-face-down-self | turn-face-down-self |  | 0 | 0.0 | 0 | 6 |
| turn-face-up | turn-face-up |  | 0 | 0.0 | 0 | 16 |
| turn-face-up-trigger | turn-face-up-trigger |  | 0 | 0.0 | 0 | 29 |
| turn-face-up-trigger-self | turn-face-up-trigger-self |  | 0 | 0.0 | 0 | 107 |
| turns-off-defender | turns off defender |  | 0 | 0.0 | 0 | 13 |
| turns-taken-matter | turns taken matter |  | 0 | 0.0 | 0 | 13 |
| tutor-artifact-colored | tutor-artifact-colored |  | 0 | 0.0 | 0 | 1 |
| tutor-artifact-creature | tutor-artifact-creature |  | 0 | 0.0 | 0 | 2 |
| tutor-artifact-food | tutor-artifact-food |  | 0 | 0.0 | 0 | 1 |
| tutor-artifact-land | tutor-artifact-land |  | 0 | 0.0 | 0 | 1 |
| tutor-artifact-legendary | tutor-artifact-legendary |  | 0 | 0.0 | 0 | 2 |
| tutor-artifact-noncreature | tutor-artifact-noncreature |  | 0 | 0.0 | 0 | 1 |
| tutor-artifact-spacecraft | tutor-artifact-spacecraft |  | 0 | 0.0 | 0 | 2 |
| tutor-artifact-vehicle | tutor-artifact-vehicle | tutor-vehicle | 0 | 0.0 | 0 | 4 |
| tutor-augment | tutor-augment |  | 0 | 0.0 | 0 | 3 |
| tutor-aura-creature | tutor-aura-creature |  | 0 | 0.0 | 0 | 1 |
| tutor-aura-curse | tutor-aura-curse | tutor-curse | 0 | 0.0 | 0 | 2 |
| tutor-battle | tutor-battle |  | 0 | 0.0 | 0 | 3 |
| tutor-black | tutor-black |  | 0 | 0.0 | 0 | 4 |
| tutor-blue | tutor-blue |  | 0 | 0.0 | 0 | 2 |
| tutor-cast | tutor-cast |  | 0 | 0.0 | 0 | 9 |
| tutor-color | tutor-color |  | 0 | 0.0 | 0 | 7 |
| tutor-creature-ally | tutor-creature-ally |  | 0 | 0.0 | 0 | 2 |
| tutor-creature-assembly-worker | tutor-creature-assembly-worker |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-aurochs | tutor-creature-aurochs | tutor-aurochs | 0 | 0.0 | 0 | 1 |
| tutor-creature-bird | tutor-creature-bird |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-colorless | tutor-creature-colorless |  | 0 | 0.0 | 0 | 3 |
| tutor-creature-construct | tutor-creature-construct | tutor-construct | 0 | 0.0 | 0 | 1 |
| tutor-creature-deathtouch | tutor-creature-deathtouch |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-demigod | tutor-creature-demigod |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-demon | tutor-creature-demon | tutor-demon | 0 | 0.0 | 0 | 3 |
| tutor-creature-dinosaur | tutor-creature-dinosaur | tutor-dinosaur | 0 | 0.0 | 0 | 4 |
| tutor-creature-doctor | tutor-creature-doctor |  | 0 | 0.0 | 0 | 5 |
| tutor-creature-dragon | tutor-creature-dragon | tutor-dragon;tutor-permanent-dragon | 0 | 0.0 | 0 | 15 |
| tutor-creature-dwarf | tutor-creature-dwarf | tutor-dwarf | 0 | 0.0 | 0 | 1 |
| tutor-creature-eldrazi | tutor-creature-eldrazi | tutor-eldrazi | 0 | 0.0 | 0 | 1 |
| tutor-creature-elemental | tutor-creature-elemental | tutor-elemental | 0 | 0.0 | 0 | 1 |
| tutor-creature-elf | tutor-creature-elf | tutor-permanent-elf;tutor-elf | 0 | 0.0 | 0 | 4 |
| tutor-creature-embalm | tutor-creature-embalm |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-eternalize | tutor-creature-eternalize |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-faerie | tutor-creature-faerie | tutor-faerie | 0 | 0.0 | 0 | 1 |
| tutor-creature-flying | tutor-creature-flying |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-giant | tutor-creature-giant | tutor-giant | 0 | 0.0 | 0 | 1 |
| tutor-creature-goblin | tutor-creature-goblin | tutor-goblin;tutor-permanent-goblin | 0 | 0.0 | 0 | 4 |
| tutor-creature-god | tutor-creature-god | tutor-god | 0 | 0.0 | 0 | 2 |
| tutor-creature-green | tutor-creature-green |  | 0 | 0.0 | 0 | 5 |
| tutor-creature-halfling | tutor-creature-halfling |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-hexproof | tutor-creature-hexproof |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-kithkin | tutor-creature-kithkin | tutor-kithkin | 0 | 0.0 | 0 | 1 |
| tutor-creature-legendary | tutor-creature-legendary |  | 0 | 0.0 | 0 | 7 |
| tutor-creature-mercenary | tutor-creature-mercenary | tutor-permanent-mercenary;tutor-mercenary | 0 | 0.0 | 0 | 11 |
| tutor-creature-merfolk | tutor-creature-merfolk | tutor-merfolk;tutor-permanent-merfolk | 0 | 0.0 | 0 | 3 |
| tutor-creature-minotaur | tutor-creature-minotaur |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-mount | tutor-creature-mount |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-myr | tutor-creature-myr |  | 0 | 0.0 | 0 | 2 |
| tutor-creature-nephilim | tutor-creature-nephilim |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-ninja | tutor-creature-ninja | tutor-ninja | 0 | 0.0 | 0 | 1 |
| tutor-creature-noble | tutor-creature-noble |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-phyrexian | tutor-creature-phyrexian |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-pirate | tutor-creature-pirate |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-power | tutor-creature-power |  | 0 | 0.0 | 0 | 3 |
| tutor-creature-praetor | tutor-creature-praetor |  | 0 | 0.0 | 0 | 2 |
| tutor-creature-rat | tutor-creature-rat | tutor-rat | 0 | 0.0 | 0 | 1 |
| tutor-creature-reach | tutor-creature-reach |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-rebel | tutor-creature-rebel |  | 0 | 0.0 | 0 | 10 |
| tutor-creature-sliver | tutor-creature-sliver |  | 0 | 0.0 | 0 | 2 |
| tutor-creature-specific | tutor-creature-specific |  | 0 | 0.0 | 0 | 2 |
| tutor-creature-sphinx | tutor-creature-sphinx |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-spirit | tutor-creature-spirit | tutor-permanent-spirit | 0 | 0.0 | 0 | 3 |
| tutor-creature-squirrel | tutor-creature-squirrel |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-toughness | tutor-creature-toughness |  | 0 | 0.0 | 0 | 3 |
| tutor-creature-trample | tutor-creature-trample |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-treefolk | tutor-creature-treefolk |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-vampire | tutor-creature-vampire | tutor-vampire | 0 | 0.0 | 0 | 1 |
| tutor-creature-vanilla | tutor-creature-vanilla |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-whale | tutor-creature-whale |  | 0 | 0.0 | 0 | 1 |
| tutor-creature-wizard | tutor-creature-wizard | tutor-wizard | 0 | 0.0 | 0 | 2 |
| tutor-creature-zombie | tutor-creature-zombie | tutor-zombie | 0 | 0.0 | 0 | 1 |
| tutor-enchantment-plan | tutor-enchantment-plan |  | 0 | 0.0 | 0 | 1 |
| tutor-enchantment-room | tutor-enchantment-room |  | 0 | 0.0 | 0 | 1 |
| tutor-enchantment-saga | tutor-enchantment-saga |  | 0 | 0.0 | 0 | 1 |
| tutor-enchantment-shrine | tutor-enchantment-shrine |  | 0 | 0.0 | 0 | 3 |
| tutor-flashback | tutor-flashback |  | 0 | 0.0 | 0 | 1 |
| tutor-from-opponent | tutor-from-opponent | tutor-opponent | 0 | 0.0 | 0 | 17 |
| tutor-green | tutor-green |  | 0 | 0.0 | 0 | 2 |
| tutor-host | tutor-host |  | 0 | 0.0 | 0 | 1 |
| tutor-instant-sorcery-arcane | tutor-instant-sorcery-arcane |  | 0 | 0.0 | 0 | 1 |
| tutor-instant-sorcery-lesson | tutor-instant-sorcery-lesson |  | 0 | 0.0 | 0 | 1 |
| tutor-instant-sorcery-trap | tutor-instant-sorcery-trap |  | 0 | 0.0 | 0 | 1 |
| tutor-interaction | tutor-interaction |  | 0 | 0.0 | 0 | 9 |
| tutor-land-basic-plains | tutor-land-basic-plains |  | 0 | 0.0 | 0 | 34 |
| tutor-land-cave | tutor-land-cave |  | 0 | 0.0 | 0 | 4 |
| tutor-land-desert | tutor-land-desert |  | 0 | 0.0 | 0 | 9 |
| tutor-land-planet | tutor-land-planet |  | 0 | 0.0 | 0 | 3 |
| tutor-land-snow | tutor-land-snow |  | 0 | 0.0 | 0 | 2 |
| tutor-land-specific | tutor-land-specific |  | 0 | 0.0 | 0 | 1 |
| tutor-land-town | tutor-land-town |  | 0 | 0.0 | 0 | 2 |
| tutor-legendary | tutor-legendary | tutor-permanent-legendary | 0 | 0.0 | 0 | 7 |
| tutor-monocolored | tutor-monocolored |  | 0 | 0.0 | 0 | 1 |
| tutor-multicolored | tutor-multicolored |  | 0 | 0.0 | 0 | 1 |
| tutor-noncreature | tutor-noncreature |  | 0 | 0.0 | 0 | 0 |
| tutor-nonland | tutor-nonland |  | 0 | 0.0 | 0 | 6 |
| tutor-permanent-snow | tutor-permanent-snow |  | 0 | 0.0 | 0 | 1 |
| tutor-planeswalker | tutor-planeswalker |  | 0 | 0.0 | 0 | 46 |
| tutor-red | tutor-red |  | 0 | 0.0 | 0 | 2 |
| tutor-rune | tutor-rune |  | 0 | 0.0 | 0 | 2 |
| tutor-self | tutor-self | self-tutor | 0 | 0.0 | 0 | 27 |
| tutor-to-exile | tutor-to-exile | tutor-exile | 0 | 0.0 | 0 | 27 |
| tutor-to-top | tutor-to-top | tutor-totop | 0 | 0.0 | 0 | 55 |
| tutor-white | tutor-white |  | 0 | 0.0 | 0 | 1 |
| typal-coupling-distinct | typal coupling-distinct |  | 0 | 0.0 | 0 | 20 |
| typal-advisor | typal-advisor | tribal-advisor | 0 | 0.0 | 0 | 3 |
| typal-aetherborn | typal-aetherborn | tribal-aetherborn | 0 | 0.0 | 0 | 1 |
| typal-alicorn | typal-alicorn | tribal-alicorn | 0 | 0.0 | 0 | 1 |
| typal-alien | typal-alien | tribal-alien | 0 | 0.0 | 0 | 1 |
| typal-ape | typal-ape | tribal-ape | 0 | 0.0 | 0 | 2 |
| typal-archer | typal-archer | tribal-archer | 0 | 0.0 | 0 | 2 |
| typal-archon | typal-archon | tribal-archon | 0 | 0.0 | 0 | 1 |
| typal-army | typal-army | tribal-army | 0 | 0.0 | 0 | 75 |
| typal-artificer | typal-artificer | tribal-artificer | 0 | 0.0 | 0 | 6 |
| typal-assassin | typal-assassin | tribal-assassin | 0 | 0.0 | 0 | 53 |
| typal-atog | typal-atog | tribal-atog | 0 | 0.0 | 0 | 1 |
| typal-aurochs | typal-aurochs | tribal-aurochs | 0 | 0.0 | 0 | 4 |
| typal-balloon | typal-balloon | tribal-balloon | 0 | 0.0 | 0 | 1 |
| typal-barbarian | typal-barbarian | lord-barbarian;tribal-barbarian | 0 | 0.0 | 0 | 2 |
| typal-bard | typal-bard | tribal-bard | 0 | 0.0 | 0 | 1 |
| typal-bat | typal-bat | tribal-bat | 0 | 0.0 | 0 | 12 |
| typal-bear | typal-bear | tribal-bear | 0 | 0.0 | 0 | 9 |
| typal-beast | typal-beast | tribal-beast | 0 | 0.0 | 0 | 26 |
| typal-beeble | typal-beeble | tribal-beeble | 0 | 0.0 | 0 | 1 |
| typal-berserker | typal-berserker | tribal-berserker | 0 | 0.0 | 0 | 4 |
| typal-bird | typal-bird | tribal-bird | 0 | 0.0 | 0 | 39 |
| typal-bison | typal-bison | tribal-bison | 0 | 0.0 | 0 | 1 |
| typal-blinkmoth | typal-blinkmoth | tribal-blinkmoth | 0 | 0.0 | 0 | 1 |
| typal-boar | typal-boar | tribal-boar | 0 | 0.0 | 0 | 6 |
| typal-brainiac | typal-brainiac | tribal-brainiac | 0 | 0.0 | 0 | 1 |
| typal-camarid | typal-camarid | tribal-camarid | 0 | 0.0 | 0 | 1 |
| typal-camel | typal-camel |  | 0 | 0.0 | 0 | 1 |
| typal-caribou | typal-caribou | tribal-caribou | 0 | 0.0 | 0 | 1 |
| typal-centaur | typal-centaur | tribal-centaur | 0 | 0.0 | 0 | 1 |
| typal-chimera | typal-chimera | tribal-chimera | 0 | 0.0 | 0 | 4 |
| typal-citizen | typal-citizen | tribal-citizen | 0 | 0.0 | 0 | 5 |
| typal-clamfolk | typal-clamfolk |  | 0 | 0.0 | 0 | 1 |
| typal-cleric | typal-cleric | tribal-cleric | 0 | 0.0 | 0 | 81 |
| typal-clown | typal-clown | tribal-clown | 0 | 0.0 | 0 | 1 |
| typal-construct | typal-construct | tribal-construct | 0 | 0.0 | 0 | 4 |
| typal-crab | typal-crab | tribal-crab | 0 | 0.0 | 0 | 4 |
| typal-crocodile | typal-crocodile |  | 0 | 0.0 | 0 | 1 |
| typal-dalek | typal-dalek | tribal-dalek | 0 | 0.0 | 0 | 4 |
| typal-demigod | typal-demigod | tribal-demigod | 0 | 0.0 | 0 | 2 |
| typal-demon | typal-demon | tribal-demon;demon synergy | 0 | 0.0 | 0 | 30 |
| typal-detective | typal-detective | tribal-detective | 0 | 0.0 | 0 | 8 |
| typal-devil | typal-devil | tribal-devil | 0 | 0.0 | 0 | 5 |
| typal-dinosaur | typal-dinosaur | dinosaur tribal;tribal-dinosaur | 0 | 0.0 | 0 | 63 |
| typal-doctor | typal-doctor | tribal-doctor | 0 | 0.0 | 0 | 16 |
| typal-dog | typal-dog | tribal-dog | 0 | 0.0 | 0 | 12 |
| typal-donkey | typal-donkey | tribal-donkey | 0 | 0.0 | 0 | 1 |
| typal-drake | typal-drake | tribal-drake | 0 | 0.0 | 0 | 1 |
| typal-druid | typal-druid | tribal-druid | 0 | 0.0 | 0 | 4 |
| typal-dwarf | typal-dwarf | tribal-dwarf | 0 | 0.0 | 0 | 28 |
| typal-each | typal-each | tribal-each | 0 | 0.0 | 0 | 11 |
| typal-egg | typal-egg | tribal-egg | 0 | 0.0 | 0 | 3 |
| typal-elder-dragon | typal-elder-dragon | tribal-elder-dragon | 0 | 0.0 | 0 | 1 |
| typal-eldrazi | typal-eldrazi | tribal-eldrazi | 0 | 0.0 | 0 | 18 |
| typal-eldrazi-scion | typal-eldrazi-scion | tribal-eldrazi-scion | 0 | 0.0 | 0 | 3 |
| typal-eldrazi-spawn | typal-eldrazi-spawn | tribal-eldrazi-spawn | 0 | 0.0 | 0 | 4 |
| typal-elephant | typal-elephant | tribal-elephant | 0 | 0.0 | 0 | 2 |
| typal-employee | typal-employee | tribal-employee | 0 | 0.0 | 0 | 2 |
| typal-eye | typal-eye | tribal-eye | 0 | 0.0 | 0 | 0 |
| typal-fish | typal-fish | tribal-fish | 0 | 0.0 | 0 | 5 |
| typal-flagbearer | typal-flagbearer | tribal-flagbearer | 0 | 0.0 | 0 | 4 |
| typal-fox | typal-fox | tribal-fox | 0 | 0.0 | 0 | 2 |
| typal-fractal | typal-fractal | tribal-fractal | 0 | 0.0 | 0 | 3 |
| typal-frog | typal-frog | tribal-frog | 0 | 0.0 | 0 | 13 |
| typal-fungus | typal-fungus | tribal-fungus | 0 | 0.0 | 0 | 10 |
| typal-gamer | typal-gamer | tribal-gamer | 0 | 0.0 | 0 | 1 |
| typal-gamma | typal-gamma |  | 0 | 0.0 | 0 | 3 |
| typal-glimmer | typal-glimmer | tribal-glimmer | 0 | 0.0 | 0 | 1 |
| typal-goblin-orc | typal-goblin-orc | typal-orc-goblin | 0 | 0.0 | 0 | 18 |
| typal-god | typal-god | tribal-god | 0 | 0.0 | 0 | 7 |
| typal-golem | typal-golem | tribal-golem | 0 | 0.0 | 0 | 11 |
| typal-gorgon | typal-gorgon | tribal-gorgon | 0 | 0.0 | 0 | 2 |
| typal-gremlin | typal-gremlin | tribal-gremlin | 0 | 0.0 | 0 | 2 |
| typal-guest | typal-guest | tribal-guest | 0 | 0.0 | 0 | 1 |
| typal-halfling | typal-halfling | tribal-halfling | 0 | 0.0 | 0 | 6 |
| typal-hamster | typal-hamster | tribal-hamster | 0 | 0.0 | 0 | 3 |
| typal-hero | typal-hero | tribal-hero | 0 | 0.0 | 0 | 44 |
| typal-homarid | typal-homarid | tribal-homarid | 0 | 0.0 | 0 | 2 |
| typal-homunculus | typal-homunculus | tribal-homunculus | 0 | 0.0 | 0 | 1 |
| typal-horror | typal-horror | tribal-horror | 0 | 0.0 | 0 | 9 |
| typal-horse | typal-horse | tribal-horse | 0 | 0.0 | 0 | 6 |
| typal-human-werewolf | typal-human-werewolf | tribal-human-werewolf | 0 | 0.0 | 0 | 1 |
| typal-hydra | typal-hydra | tribal-hydra | 0 | 0.0 | 0 | 2 |
| typal-illusion | typal-illusion | tribal-illusion | 0 | 0.0 | 0 | 8 |
| typal-imp | typal-imp | tribal-imp | 0 | 0.0 | 0 | 4 |
| typal-insect | typal-insect | tribal-insect | 0 | 0.0 | 0 | 13 |
| typal-jackal | typal-jackal |  | 0 | 0.0 | 0 | 1 |
| typal-jellyfish | typal-jellyfish |  | 0 | 0.0 | 0 | 1 |
| typal-juggernaut | typal-juggernaut | tribal-juggernaut | 0 | 0.0 | 0 | 1 |
| typal-kavu | typal-kavu | tribal-kavu | 0 | 0.0 | 0 | 7 |
| typal-killbot | typal-killbot | tribal-killbot | 0 | 0.0 | 0 | 1 |
| typal-klingon | typal-klingon |  | 0 | 0.0 | 0 | 13 |
| typal-knight | typal-knight | tribal-knight;synergy-knight | 0 | 0.0 | 0 | 50 |
| typal-kobold | typal-kobold | tribal-kobold | 0 | 0.0 | 0 | 4 |
| typal-kor | typal-kor | tribal-kor | 0 | 0.0 | 0 | 1 |
| typal-kraken | typal-kraken | tribal-kraken | 0 | 0.0 | 0 | 12 |
| typal-leech | typal-leech | tribal-leech | 0 | 0.0 | 0 | 2 |
| typal-leviathan | typal-leviathan | tribal-leviathan | 0 | 0.0 | 0 | 10 |
| typal-lhurgoyf | typal-lhurgoyf | tribal-lhurgoyf | 0 | 0.0 | 0 | 3 |
| typal-lizard | typal-lizard | tribal-lizard;typal-viashino;tribal-viashino | 0 | 0.0 | 0 | 12 |
| typal-lobster | typal-lobster |  | 0 | 0.0 | 0 | 2 |
| typal-lupine | typal-lupine | typal-wolves-and-werewolves | 0 | 0.0 | 0 | 27 |
| typal-mercenary | typal-mercenary | tribal-mercenary | 0 | 0.0 | 0 | 33 |
| typal-minion | typal-minion | tribal-minion | 0 | 0.0 | 0 | 1 |
| typal-minotaur | typal-minotaur | tribal-minotaur | 0 | 0.0 | 0 | 14 |
| typal-monk | typal-monk | tribal-monk | 0 | 0.0 | 0 | 1 |
| typal-monkey | typal-monkey | tribal-monkey | 0 | 0.0 | 0 | 1 |
| typal-moogle | typal-moogle | tribal-moogle | 0 | 0.0 | 0 | 2 |
| typal-moonfolk | typal-moonfolk | tribal-moonfolk | 0 | 0.0 | 0 | 1 |
| typal-mount | typal-mount | tribal-mount | 0 | 0.0 | 0 | 38 |
| typal-mouse | typal-mouse | tribal-mouse | 0 | 0.0 | 0 | 13 |
| typal-multi-sea-monster | typal-multi-sea-monster | tribal-multi-sea-monster | 0 | 0.0 | 0 | 9 |
| typal-mutant | typal-mutant | tribal-mutant | 0 | 0.0 | 0 | 18 |
| typal-mutant-ninja-turtle | typal-mutant-ninja-turtle |  | 0 | 0.0 | 0 | 5 |
| typal-myr | typal-myr | tribal-myr | 0 | 0.0 | 0 | 7 |
| typal-nautilid | typal-nautilid | tribal-nautilid | 0 | 0.0 | 0 | 1 |
| typal-nautilus | typal-nautilus |  | 0 | 0.0 | 0 | 2 |
| typal-neo-solo-attack | typal-neo-solo-attack |  | 0 | 0.0 | 0 | 11 |
| typal-nephilim | typal-nephilim |  | 0 | 0.0 | 0 | 1 |
| typal-nightmare | typal-nightmare | tribal-nightmare | 0 | 0.0 | 0 | 5 |
| typal-nightstalker | typal-nightstalker | tribal-nightstalker | 0 | 0.0 | 0 | 1 |
| typal-ninja | typal-ninja | tribal-ninja | 0 | 0.0 | 0 | 28 |
| typal-noble | typal-noble |  | 0 | 0.0 | 0 | 1 |
| typal-non-angel | typal-non-angel | tribal-non-angel | 0 | 0.0 | 0 | 2 |
| typal-non-archon | typal-non-archon | tribal-non-archon | 0 | 0.0 | 0 | 1 |
| typal-non-assassin | typal-non-assassin | tribal-non-assassin | 0 | 0.0 | 0 | 1 |
| typal-non-borg | typal-non-borg |  | 0 | 0.0 | 0 | 7 |
| typal-non-faerie | typal-non-faerie |  | 0 | 0.0 | 0 | 1 |
| typal-non-horse | typal-non-horse | tribal-non-horse | 0 | 0.0 | 0 | 1 |
| typal-non-kree | typal-non-kree |  | 0 | 0.0 | 0 | 1 |
| typal-non-lemur | typal-non-lemur |  | 0 | 0.0 | 0 | 1 |
| typal-non-pilot | typal-non-pilot |  | 0 | 0.0 | 0 | 1 |
| typal-non-share | typal-non-share | tribal-non-share | 0 | 0.0 | 0 | 7 |
| typal-non-spirit | typal-non-spirit | tribal-non-spirit | 0 | 0.0 | 0 | 3 |
| typal-non-villain | typal-non-villain |  | 0 | 0.0 | 0 | 1 |
| typal-non-wall | typal-non-wall |  | 0 | 0.0 | 0 | 5 |
| typal-non-zombie | typal-non-zombie | tribal-non-zombie | 0 | 0.0 | 0 | 1 |
| typal-octopus | typal-octopus | typal-cephalid;tribal-octopus | 0 | 0.0 | 0 | 13 |
| typal-officer | typal-officer |  | 0 | 0.0 | 0 | 6 |
| typal-ogre | typal-ogre | tribal-ogre | 0 | 0.0 | 0 | 5 |
| typal-ooze | typal-ooze | tribal-ooze | 0 | 0.0 | 0 | 7 |
| typal-orc | typal-orc | tribal-orc | 0 | 0.0 | 0 | 20 |
| typal-otter | typal-otter | tribal-otter | 0 | 0.0 | 0 | 12 |
| typal-outlaw | typal-outlaw | tribal-outlaw | 0 | 0.0 | 0 | 19 |
| typal-ox | typal-ox | tribal-ox | 0 | 0.0 | 0 | 2 |
| typal-oyster | typal-oyster |  | 0 | 0.0 | 0 | 1 |
| typal-pegasus | typal-pegasus | tribal-pegasus | 0 | 0.0 | 0 | 4 |
| typal-pentavite | typal-pentavite | tribal-pentavite | 0 | 0.0 | 0 | 1 |
| typal-performer | typal-performer | tribal-performer | 0 | 0.0 | 0 | 1 |
| typal-pest | typal-pest | tribal-pest | 0 | 0.0 | 0 | 4 |
| typal-phoenix | typal-phoenix | tribal-phoenix | 0 | 0.0 | 0 | 3 |
| typal-phyrexian | typal-phyrexian | tribal-phyrexian | 0 | 0.0 | 0 | 25 |
| typal-pilot | typal-pilot | tribal-pilot | 0 | 0.0 | 0 | 2 |
| typal-pirate | typal-pirate | tribal-pirate | 0 | 0.0 | 0 | 67 |
| typal-plant | typal-plant | tribal-plant | 0 | 0.0 | 0 | 5 |
| typal-pony | typal-pony | tribal-pony | 0 | 0.0 | 0 | 1 |
| typal-praetor | typal-praetor | tribal-praetor | 0 | 0.0 | 0 | 3 |
| typal-prism | typal-prism |  | 0 | 0.0 | 0 | 1 |
| typal-rabbit | typal-rabbit | tribal-rabbit | 0 | 0.0 | 0 | 9 |
| typal-raccoon | typal-raccoon | tribal-raccoon | 0 | 0.0 | 0 | 8 |
| typal-rat | typal-rat | tribal-rat | 0 | 0.0 | 0 | 38 |
| typal-rebel | typal-rebel | tribal-rebel | 0 | 0.0 | 0 | 14 |
| typal-reflection | typal-reflection | tribal-reflection | 0 | 0.0 | 0 | 1 |
| typal-reveler | typal-reveler | tribal-reveler | 0 | 0.0 | 0 | 4 |
| typal-rhino | typal-rhino |  | 0 | 0.0 | 0 | 1 |
| typal-rigger | typal-rigger | tribal-rigger | 0 | 0.0 | 0 | 1 |
| typal-robot | typal-robot | tribal-robot | 0 | 0.0 | 0 | 10 |
| typal-rogue | typal-rogue | tribal-rogue | 0 | 0.0 | 0 | 97 |
| typal-salamander | typal-salamander | tribal-salamander | 0 | 0.0 | 0 | 2 |
| typal-samurai | typal-samurai | tribal-samurai | 0 | 0.0 | 0 | 23 |
| typal-saproling | typal-saproling | tribal-saproling;lord-saproling | 0 | 0.0 | 0 | 24 |
| typal-satyr | typal-satyr | tribal-satyr | 0 | 0.0 | 0 | 1 |
| typal-scarecrow | typal-scarecrow | tribal-scarecrow | 0 | 0.0 | 0 | 2 |
| typal-scientist | typal-scientist |  | 0 | 0.0 | 0 | 1 |
| typal-scion | typal-scion | tribal-scion | 0 | 0.0 | 0 | 1 |
| typal-scout | typal-scout | tribal-scout | 0 | 0.0 | 0 | 1 |
| typal-sculpture | typal-sculpture | tribal-sculpture | 0 | 0.0 | 0 | 1 |
| typal-seal | typal-seal |  | 0 | 0.0 | 0 | 2 |
| typal-serpent | typal-serpent | tribal-serpent | 0 | 0.0 | 0 | 15 |
| typal-servo | typal-servo | tribal-servo | 0 | 0.0 | 0 | 2 |
| typal-shade | typal-shade | tribal-shade | 0 | 0.0 | 0 | 1 |
| typal-shaman | typal-shaman | tribal-shaman | 0 | 0.0 | 0 | 13 |
| typal-shapeshifter | typal-shapeshifter | tribal-shapeshifter | 0 | 0.0 | 0 | 3 |
| typal-shark | typal-shark | tribal-shark | 0 | 0.0 | 0 | 3 |
| typal-shrimp | typal-shrimp |  | 0 | 0.0 | 0 | 1 |
| typal-skeleton | typal-skeleton | tribal-skeleton | 0 | 0.0 | 0 | 7 |
| typal-sliver | typal-sliver | tribal-sliver | 0 | 0.0 | 0 | 121 |
| typal-slug | typal-slug | tribal-slug | 0 | 0.0 | 0 | 3 |
| typal-snail | typal-snail | tribal-snail | 0 | 0.0 | 0 | 1 |
| typal-snake | typal-snake | tribal-snake | 0 | 0.0 | 0 | 16 |
| typal-sneaky | typal-sneaky |  | 0 | 0.0 | 0 | 4 |
| typal-spawn | typal-spawn | tribal-spawn | 0 | 0.0 | 0 | 1 |
| typal-specter | typal-specter | tribal-specter | 0 | 0.0 | 0 | 1 |
| typal-sphinx | typal-sphinx | tribal-sphinx | 0 | 0.0 | 0 | 4 |
| typal-sponge | typal-sponge |  | 0 | 0.0 | 0 | 1 |
| typal-squid | typal-squid |  | 0 | 0.0 | 0 | 1 |
| typal-squirrel | typal-squirrel | tribal-squirrel | 0 | 0.0 | 0 | 30 |
| typal-starfish | typal-starfish |  | 0 | 0.0 | 0 | 2 |
| typal-survivor | typal-survivor | tribal-survivor | 0 | 0.0 | 0 | 1 |
| typal-symbiote | typal-symbiote | tribal-symbiote | 0 | 0.0 | 0 | 1 |
| typal-teddy-bear | typal-teddy-bear | tribal-teddy-bear | 0 | 0.0 | 0 | 1 |
| typal-tentacle | typal-tentacle | tribal-tentacle | 0 | 0.0 | 0 | 1 |
| typal-thrull | typal-thrull | tribal-thrull | 0 | 0.0 | 0 | 4 |
| typal-tiefling | typal-tiefling | tribal-tiefling | 0 | 0.0 | 0 | 2 |
| typal-time-lord | typal-time-lord |  | 0 | 0.0 | 0 | 4 |
| typal-transformer | typal-transformer | tribal-transformer | 0 | 0.0 | 0 | 1 |
| typal-tribble | typal-tribble |  | 0 | 0.0 | 0 | 1 |
| typal-trilobite | typal-trilobite |  | 0 | 0.0 | 0 | 2 |
| typal-turtle | typal-turtle | tribal-turtle | 0 | 0.0 | 0 | 12 |
| typal-tyranid | typal-tyranid | tribal-tyranid | 0 | 0.0 | 0 | 1 |
| typal-unicorn | typal-unicorn | tribal-unicorn | 0 | 0.0 | 0 | 3 |
| typal-vulcan | typal-vulcan |  | 0 | 0.0 | 0 | 1 |
| typal-wall | typal-wall | tribal-wall | 0 | 0.0 | 0 | 13 |
| typal-walrus | typal-walrus |  | 0 | 0.0 | 0 | 1 |
| typal-warlock | typal-warlock | tribal-warlock | 0 | 0.0 | 0 | 24 |
| typal-warrior | typal-warrior | tribal-warrior | 0 | 0.0 | 0 | 120 |
| typal-whale | typal-whale |  | 0 | 0.0 | 0 | 3 |
| typal-wolf | typal-wolf | tribal-wolf | 0 | 0.0 | 0 | 41 |
| typal-worm | typal-worm | tribal-worm | 0 | 0.0 | 0 | 1 |
| typal-wraith | typal-wraith | tribal-wraith | 0 | 0.0 | 0 | 4 |
| typal-wurm | typal-wurm | tribal-wurm | 0 | 0.0 | 0 | 2 |
| typal-zubera | typal-zubera | tribal-zubera | 0 | 0.0 | 0 | 5 |
| type-addition-frog | type addition frog |  | 0 | 0.0 | 0 | 6 |
| type-addition-rabbit | type addition rabbit |  | 0 | 0.0 | 0 | 2 |
| type-addition-sorcerer | type addition sorcerer |  | 0 | 0.0 | 0 | 23 |
| type-errata-cephalid | type errata cephalid |  | 0 | 0.0 | 0 | 25 |
| type-errata-cheetah | type errata cheetah |  | 0 | 0.0 | 0 | 3 |
| type-errata-chicken | type errata chicken |  | 0 | 0.0 | 0 | 4 |
| type-errata-cobra | type errata cobra |  | 0 | 0.0 | 0 | 3 |
| type-errata-dinosaur | type errata dinosaur |  | 0 | 0.0 | 0 | 16 |
| type-errata-falcon | type errata falcon |  | 0 | 0.0 | 0 | 6 |
| type-errata-ghost | type errata ghost |  | 0 | 0.0 | 0 | 6 |
| type-errata-ghoul | type errata ghoul |  | 0 | 0.0 | 0 | 3 |
| type-errata-mammoth | type errata mammoth |  | 0 | 0.0 | 0 | 2 |
| type-errata-roc | type errata roc |  | 0 | 0.0 | 0 | 2 |
| type-errata-shark | type errata shark |  | 0 | 0.0 | 0 | 5 |
| type-errata-specific-ape | type errata specific ape |  | 0 | 0.0 | 0 | 6 |
| type-errata-specific-bird | type errata specific bird |  | 0 | 0.0 | 0 | 21 |
| type-errata-specific-horse | type errata specific horse |  | 0 | 0.0 | 0 | 5 |
| type-errata-specific-insect | type errata specific insect |  | 0 | 0.0 | 0 | 8 |
| type-errata-specific-ouphe | type errata specific ouphe |  | 0 | 0.0 | 0 | 3 |
| type-errata-specific-snake | type errata specific snake |  | 0 | 0.0 | 0 | 6 |
| type-errata-specific-spirit | type errata specific spirit |  | 0 | 0.0 | 0 | 10 |
| type-errata-specific-wizard | type errata specific wizard |  | 0 | 0.0 | 0 | 4 |
| type-errata-specific-yeti | type errata specific yeti |  | 0 | 0.0 | 0 | 2 |
| type-errata-specific-zombie | type errata specific zombie |  | 0 | 0.0 | 0 | 6 |
| type-errata-vulture | type errata vulture |  | 0 | 0.0 | 0 | 2 |
| type-removal-cat-rakshasa | type removal cat rakshasa |  | 0 | 0.0 | 0 | 6 |
| un-type-line | un type line | silver border type line | 0 | 0.0 | 0 | 70 |
| un-color | un-color | uncolor | 0 | 0.0 | 0 | 12 |
| un-design | un-design |  | 0 | 0.0 | 0 | 428 |
| un-forecast | un-forecast |  | 0 | 0.0 | 0 | 21 |
| un-keyword | un-keyword |  | 0 | 0.0 | 0 | 23 |
| un-set-mechanics | un-set mechanics | silver border mechanics | 0 | 0.0 | 0 | 422 |
| unblocked-trigger | unblocked trigger |  | 0 | 0.0 | 0 | 44 |
| undaunted | undaunted |  | 0 | 0.0 | 0 | 6 |
| unheroic | unheroic |  | 0 | 0.0 | 0 | 59 |
| unique-counters-matter | unique counters matter |  | 0 | 0.0 | 0 | 8 |
| unique-cr-reference | unique cr reference |  | 0 | 0.0 | 0 | 73 |
| unique-creature-type | unique creature type |  | 0 | 0.0 | 0 | 71 |
| unique-doubler | unique doubler |  | 0 | 0.0 | 0 | 4 |
| unique-enchant-target | unique enchant target |  | 0 | 0.0 | 0 | 34 |
| unique-keyword | unique keyword |  | 0 | 0.0 | 0 | 68 |
| unique-mana-symbol | unique mana symbol |  | 0 | 0.0 | 0 | 10 |
| unique-noncreature-token | unique noncreature token |  | 0 | 0.0 | 0 | 25 |
| unique-plane-type | unique plane type |  | 0 | 0.0 | 0 | 72 |
| unique-planeswalker-type | unique planeswalker type |  | 0 | 0.0 | 0 | 43 |
| unique-token | unique token |  | 0 | 0.0 | 0 | 393 |
| unique-token-type | unique token type |  | 0 | 0.0 | 0 | 5 |
| unspent-mana-matters | unspent mana matters |  | 0 | 0.0 | 0 | 3 |
| unstable-killbot | unstable killbot |  | 0 | 0.0 | 0 | 4 |
| unstable-secret-base | unstable secret base |  | 0 | 0.0 | 0 | 1 |
| unstable-variant | unstable variant |  | 0 | 0.0 | 0 | 46 |
| untapper-equipment | untapper-equipment |  | 0 | 0.0 | 0 | 1 |
| untapper-nonland | untapper-nonland |  | 0 | 0.0 | 0 | 12 |
| untapper-planeswalker | untapper-planeswalker |  | 0 | 0.0 | 0 | 1 |
| unusual-landwalk | unusual landwalk |  | 0 | 0.0 | 0 | 5 |
| uril-ability | uril ability |  | 0 | 0.0 | 0 | 16 |
| vigilance-counter | vigilance counter |  | 0 | 0.0 | 0 | 20 |
| vigor-effect | vigor effect |  | 0 | 0.0 | 0 | 14 |
| voting | voting |  | 0 | 0.0 | 0 | 35 |
| wannabe-dark-confidant | wannabe dark confidant | dark confidant ability | 0 | 0.0 | 0 | 16 |
| warlord | warlord |  | 0 | 0.0 | 0 | 84 |
| watermark-matters | watermark matters |  | 0 | 0.0 | 0 | 13 |
| wedgeland | wedgeland | cycle-wedgeland | 0 | 0.0 | 0 | 13 |
| wheel-symmetrical-optional | wheel-symmetrical-optional |  | 0 | 0.0 | 0 | 11 |
| whirlpool | whirlpool |  | 0 | 0.0 | 0 | 36 |
| white-elephant | white elephant |  | 0 | 0.0 | 0 | 18 |
| wish | wish | tutor-sideboard | 0 | 0.0 | 0 | 77 |
| worship | worship | sustaining spirit | 0 | 0.0 | 0 | 11 |
| wth-storyline-in-cards | wth-storyline-in-cards |  | 0 | 0.0 | 0 | 17 |
| x-doesn't-matter | x doesn't matter |  | 0 | 0.0 | 0 | 12 |
| y-value | y value |  | 0 | 0.0 | 0 | 6 |
| you-make-the-card | you make the card |  | 0 | 0.0 | 0 | 4 |
| you-matter | you matter | physical aspects matter | 0 | 0.0 | 0 | 19 |
| your-sacrifice-matters | your sacrifice matters |  | 0 | 0.0 | 0 | 121 |
| zoo | zoo |  | 0 | 0.0 | 0 | 21 |
