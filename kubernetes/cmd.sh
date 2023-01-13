set -e
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
_PATH=$SCRIPTPATH/$2
shopt -s expand_aliases
source ~/.bash_aliases
for yml in $_PATH/*/*.yaml
do
    echo $yml
    envsubst < $yml | kl $1 -f -
done