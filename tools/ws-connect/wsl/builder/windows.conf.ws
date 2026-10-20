# 2026-10-21 ザラ「全部署共通で3コマンダーが1番左」「窓のメニューは削除していい」: 1 Codex01 2 Claude01 3 Grok01 → 4〜9 お付き (CL→GR→CD)。0 MENU 窓は廃止 (机の一覧は帯の[端末]から)。上の古い説明よりこの行が優先。
1|WSCD01 Codexコマンダー|$HOME/ai/codex|"$CD" -c check_for_update_on_startup=false -s danger-full-access -a never -m gpt-6.1-sol -c 'model_reasoning_effort="low"'; exec bash -l
2|WSCL01 Claudeコマンダー|$HOME/ai/builder|"$CL" --model fable --permission-mode bypassPermissions --continue --name "WSCL01 Claudeコマンダー" --remote-control "WSCL01 Claudeコマンダー" || "$CL" --model fable --permission-mode bypassPermissions --name "WSCL01 Claudeコマンダー" --remote-control "WSCL01 Claudeコマンダー"; exec bash -l
3|WSGR01 Grokコマンダー|$HOME/ai/grok|"$GR" --permission-mode bypassPermissions; exec bash -l
4|WSCL02 助さん|$HOME/ai/hands/02|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL02 助さん" --remote-control "WSCL02 助さん" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL02 助さん" --remote-control "WSCL02 助さん"; exec bash -l
5|WSCL03 格さん|$HOME/ai/hands/03|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL03 格さん" --remote-control "WSCL03 格さん" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL03 格さん" --remote-control "WSCL03 格さん"; exec bash -l
6|WSGR02 金さん|$HOME/ai/grok/02|"$GR" --permission-mode bypassPermissions; exec bash -l
7|WSGR03 銀さん|$HOME/ai/grok/03|"$GR" --permission-mode bypassPermissions; exec bash -l
8|WSCD02 次元|$HOME/ai/codex/02|"$CD" -c check_for_update_on_startup=false -s danger-full-access -a never; exec bash -l
9|WSCD03 五右衛門|$HOME/ai/codex/03|"$CD" -s danger-full-access -a never; exec bash -l
10|WSCL05 さなくろ|$HOME/ai/hands/05|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL05 さなくろ" --remote-control "WSCL05 さなくろ" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL05 さなくろ" --remote-control "WSCL05 さなくろ"; exec bash -l
11|WSGR05 さな|$HOME/ai/hisho/grok/05|$HOME/ai/bin/hisho-grok.sh 05; exec bash -l
12|WSCD05 さなこ|$HOME/ai/hisho/codex/05|$HOME/ai/bin/hisho-codex.sh 05; exec bash -l
13|WSCL04 えまくろ|$HOME/ai/hands/04|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL04 えまくろ" --remote-control "WSCL04 えまくろ" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL04 えまくろ" --remote-control "WSCL04 えまくろ"; exec bash -l
14|WSGR04 えま|$HOME/ai/hisho/grok/04|$HOME/ai/bin/hisho-grok.sh 04; exec bash -l
15|WSCD04 えまこ|$HOME/ai/hisho/codex/04|$HOME/ai/bin/hisho-codex.sh 04; exec bash -l
16|WSCL06 みおくろ|$HOME/ai/hands/06|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL06 みおくろ" --remote-control "WSCL06 みおくろ" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL06 みおくろ" --remote-control "WSCL06 みおくろ"; exec bash -l
17|WSGR06 みお|$HOME/ai/hisho/grok/06|$HOME/ai/bin/hisho-grok.sh 06; exec bash -l
18|WSCD06 みおこ|$HOME/ai/hisho/codex/06|$HOME/ai/bin/hisho-codex.sh 06; exec bash -l
19|WSCL07 はるくろ|$HOME/ai/hisho/claude/07|$HOME/ai/bin/hisho-leader-claude.sh; exec bash -l
20|WSGR07 はると|$HOME/ai/hisho/grok/07|$HOME/ai/bin/hisho-leader-grok.sh; exec bash -l
21|WSCD07 はると|$HOME/ai/hisho/leader|"$CD" -s danger-full-access -a never -C $HOME/ai/hisho/leader; exec bash -l
22|WSCL09 ビルダー|$HOME/Code/thelifeplan-builder|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL09 ビルダー" --remote-control "WSCL09 ビルダー" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL09 ビルダー" --remote-control "WSCL09 ビルダー"; exec bash -l
23|WSGR09 ビルダー|$HOME/Code/thelifeplan-builder-grok|$HOME/ai/bin/builder-ai.sh grok; exec bash -l
24|WSCD09 ビルダー|$HOME/Code/thelifeplan-builder-codex|$HOME/ai/bin/builder-ai.sh codex; exec bash -l
25|WSCL10 マネークラフト|$HOME/Code/moneycraft|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL10 マネークラフト" --remote-control "WSCL10 マネークラフト" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL10 マネークラフト" --remote-control "WSCL10 マネークラフト"; exec bash -l
26|WSCD10 マネークラフト|$HOME/Code/moneycraft|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/moneycraft; exec bash -l
27|WSCL11 マネーゲーム|$HOME/Code/moneygame|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL11 マネーゲーム" --remote-control "WSCL11 マネーゲーム" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL11 マネーゲーム" --remote-control "WSCL11 マネーゲーム"; exec bash -l
28|WSCD11 マネーゲーム|$HOME/Code/moneygame|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/moneygame; exec bash -l
29|WSCL34 法人化|$HOME/Code/houjinka|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL34 法人化" --remote-control "WSCL34 法人化" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL34 法人化" --remote-control "WSCL34 法人化"; exec bash -l
30|WSCD34 法人化|$HOME/Code/houjinka|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/houjinka; exec bash -l
31|WSCL40 koma|$HOME/Code/koma|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL40 koma" --remote-control "WSCL40 koma" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL40 koma" --remote-control "WSCL40 koma"; exec bash -l
32|WSCD40 koma|$HOME/Code/koma|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/koma; exec bash -l
33|WSCL42 代理店|$HOME/Code/agency|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL42 代理店" --remote-control "WSCL42 代理店" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL42 代理店" --remote-control "WSCL42 代理店"; exec bash -l
34|WSCD42 代理店|$HOME/Code/agency|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/agency; exec bash -l
35|WSCL45 kura|$HOME/Code/kura|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL45 kura" --remote-control "WSCL45 kura" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL45 kura" --remote-control "WSCL45 kura"; exec bash -l
36|WSCD45 kura|$HOME/Code/kura|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/kura; exec bash -l
37|WSCL46 保険業法|$HOME/Code/hoken|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL46 保険業法" --remote-control "WSCL46 保険業法" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL46 保険業法" --remote-control "WSCL46 保険業法"; exec bash -l
38|WSCD46 保険業法|$HOME/Code/hoken|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/hoken; exec bash -l
39|WSCL47 health|$HOME/Code/health|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL47 health" --remote-control "WSCL47 health" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL47 health" --remote-control "WSCL47 health"; exec bash -l
40|WSGR47 health|$HOME/Code/health|$HOME/ai/bin/health-ai.sh grok
41|WSCD47 health|$HOME/Code/health|$HOME/ai/bin/health-ai.sh codex
42|WSCL48 スケジュール|$HOME/Code/schedule|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL48 スケジュール" --remote-control "WSCL48 スケジュール" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL48 スケジュール" --remote-control "WSCL48 スケジュール"; exec bash -l
43|WSCD48 スケジュール|$HOME/Code/schedule|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/schedule; exec bash -l
44|WSCL49 自分レベル上げ|$HOME/Code/levelup|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL49 自分レベル上げ" --remote-control "WSCL49 自分レベル上げ" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL49 自分レベル上げ" --remote-control "WSCL49 自分レベル上げ"; exec bash -l
45|WSCD49 自分レベル上げ|$HOME/Code/levelup|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/levelup; exec bash -l
46|WSCL50 診断ラボ|$HOME/Code/shindan-lab|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL50 診断ラボ" --remote-control "WSCL50 診断ラボ" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL50 診断ラボ" --remote-control "WSCL50 診断ラボ"; exec bash -l
47|WSCL51 コールセンター|$HOME/Code/callcenter|"$CL" --permission-mode bypassPermissions --model opus --continue --name "WSCL51 コールセンター" --remote-control "WSCL51 コールセンター" || "$CL" --permission-mode bypassPermissions --model opus --name "WSCL51 コールセンター" --remote-control "WSCL51 コールセンター"; exec bash -l
48|WSCD51 コールセンター|$HOME/Code/callcenter|"$CD" -m gpt-6.1-sol -c 'model_reasoning_effort="low"' -s danger-full-access -a never -C $HOME/Code/callcenter; exec bash -l
49|WSCL53 ayako|$HOME/ai/desks/ayako/claude|$HOME/ai/bin/ayako-ai.sh claude; exec bash -l
50|WSGR53 ayako|$HOME/ai/desks/ayako/grok|$HOME/ai/bin/ayako-ai.sh grok; exec bash -l
51|WSCD53 ayako|$HOME/ai/desks/ayako/codex|$HOME/ai/bin/ayako-ai.sh codex; exec bash -l
52|WSCL54 新聞デスク|$HOME/ai/desks/yomimono/claude|$HOME/ai/bin/yomimono-ai.sh claude; exec bash -l
53|WSGR54 新聞デスク|$HOME/ai/desks/yomimono/grok|$HOME/ai/bin/yomimono-ai.sh grok; exec bash -l
54|WSCD54 新聞デスク|$HOME/ai/desks/yomimono/codex|$HOME/ai/bin/yomimono-ai.sh codex; exec bash -l
55|WSCL57 YouTube|$HOME/Code/youtube|$HOME/ai/bin/youtube-ai.sh claude; exec bash -l
56|WSCD57 YouTube|$HOME/Code/youtube|$HOME/ai/bin/youtube-ai.sh codex; exec bash -l
99|WSSH コマンド|$HOME|exec bash -l
