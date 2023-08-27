# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
LS_COLORS=:'ow=34;40:' ; export LS_COLORS
alias python='python3.11'
alias pip='pip3.11'
git secrets --install
git secrets --register-aws
. ~/.bash_profile
