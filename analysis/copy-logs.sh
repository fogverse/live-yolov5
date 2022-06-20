ROOT_PROJECT=/home/ariqbasyar/Documents/kuliah/term_8/tugas_akhir/fogverse
TO=$ROOT_PROJECT/analysis/$1/
echo WARNING! selected folder $1
echo WARNING! copying logs to $TO
set -xe
sleep 10
scp debian-camera:~/fogverse/logs/log_MyFrameProducer.csv $TO
scp raspi:~/fogverse/logs/log_MyPreprocess.csv $TO
scp jetson:~/fogverse/logs/log_MyJetson.csv $TO
scp jetson:~/fogverse/logs/log_MyJetsonScenario1.csv $TO
scp gcloud-server-1:~/fogverse/logs/log_MyCloud.csv $TO
scp debian-master:~/fogverse/logs/log_MyForwarder.csv $TO
scp debian-master:~/fogverse/logs/log_MyMerger.csv $TO
