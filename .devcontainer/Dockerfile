FROM public.ecr.aws/aws-mde/universal-image:1.0
RUN sudo yum remove -y openssl-devel
RUN sudo yum install gcc make patch zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl11 openssl11-devel tk-devel libffi-devel xz-devel -y && \
    cd /tmp && \
    wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz && \
    tar xzf Python-3.11.4.tgz && \
    cd Python-3.11.4 && \
    sudo ./configure --enable-optimizations && \
    sudo make altinstall
RUN sudo mkdir /etc/install
COPY requirements-dev.txt /etc/install
COPY .bash_profile /etc/install
COPY .bashrc /etc/install
RUN pip3.11 install --upgrade pip && \
    pip3.11 install -r /etc/install/requirements-dev.txt && \
    sudo ln -sf  /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    sudo cp /etc/install/.bash_profile ~/.bash_profile && \
    sudo cp /etc/install/.bashrc ~/.bashrc
RUN npm install -g aws-cdk @go-task/cli @aws-cdk/integ-runner