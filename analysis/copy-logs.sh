ROOT_PROJECT=/home/ariqbasyar/Documents/kuliah/term_8/tugas_akhir/fogverse
TO=$ROOT_PROJECT/analysis/$1/
echo WARNING! selected folder $1
echo WARNING! copying logs to $TO
set -xe
sleep 10
scp debian-camera:~/fogverse/logs/log_MyInput.csv $TO
scp raspi:~/fogverse/logs/log_MyPreprocess.csv $TO
scp jetson:~/fogverse/logs/log_MyJetson.csv $TO
scp gcloud-server-1:~/fogverse/logs/log_MyCloud.csv $TO
cp $ROOT_PROJECT/master/message_forwarder/logs/log_MyForwarder.csv $TO
cp $ROOT_PROJECT/master/inference_merger/logs/log_MyMerger.csv $TO
