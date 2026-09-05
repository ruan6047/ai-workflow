# OPS-CLEANUP-SMOKE2（拋棄式）

供 ai-workflow#25 R3 的條件式刪除（--force-with-lease）在真實 GitHub 遠端上走完一次成功路徑。
用完即由 release --cleanup 收掉；若它還在，代表收尾沒跑完。
