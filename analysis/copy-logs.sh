ROOT_PROJECT=/home/ariqbasyar/Documents/kuliah/term_8/tugas_akhir/fogverse
TO=$ROOT_PROJECT/analysis/$1/scenario-$2/
echo WARNING! selected folder $1
echo WARNING! copying logs to $TO
set -xe
sleep 10

case $2 in
    1)
        # skenario 1
        scp jetson:~/fogverse/logs/log_MyJetsonSc1.csv $TO
        ;;
    2)
        # skenario 2
        scp debian-camera:~/fogverse/logs/log_MyFrameProducerSc2_4.csv $TO
        scp jetson:~/fogverse/logs/log_MyJetsonSc2.csv $TO
        cp $ROOT_PROJECT/client/logs/log_MyClient.csv $TO
        ;;
    3)
        # skenario 3
        scp debian-camera:~/fogverse/logs/log_MyFrameProducerSc3.csv $TO
        scp gcloud-server-1:~/fogverse/logs/log_MyCloudSc3.csv $TO
        cp $ROOT_PROJECT/client/logs/log_MyClient.csv $TO
        ;;
    4)
        # skenario 4
        scp debian-camera:~/fogverse/logs/log_MyFrameProducerSc2_4.csv $TO
        scp raspi:~/fogverse/logs/log_MyPreprocess.csv $TO
        scp jetson:~/fogverse/logs/log_MyJetsonSc4.csv $TO
        scp gcloud-server-1:~/fogverse/logs/log_MyCloudSc4.csv $TO
        scp debian-master:~/fogverse/logs/log_MyForwarder.csv $TO
        scp debian-master:~/fogverse/logs/log_MyMerger.csv $TO
        cp $ROOT_PROJECT/client/logs/log_MyClient.csv $TO
        ;;
    *)
        echo "unknown scenario"
        ;;
esac
