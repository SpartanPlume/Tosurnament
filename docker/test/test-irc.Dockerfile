FROM inspircd/inspircd-docker

RUN mkdir -p inspircd/conf.d
RUN echo -e '<module name="connflood">\n<module name="connectban">\n<limits maxnick="40">\n<connect allow="*" useconnflood="no" useconnectban="no">' > /inspircd/conf.d/additional_settings.conf
