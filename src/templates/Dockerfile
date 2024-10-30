FROM #<FROM_BASEIMAGE>

#<USER_CREATE>
WORKDIR /bridge_setup

COPY start-bridgeclient.sh drivers_download.sh drivers_install.sh /bridge_setup/
#<COPY_DRIVER_FILES>

RUN cd /bridge_setup && chmod +x *.sh && \
    ./drivers_download.sh && \
    ./drivers_install.sh

# Install the Tableau Bridge RPM
ARG BRIDGERPM
COPY $BRIDGERPM /bridge_setup
RUN cd /bridge_setup && chmod +x $BRIDGERPM && ACCEPT_EULA=y yum localinstall -y $BRIDGERPM && rm -f $BRIDGERPM

# Copy in custom TabBridgeClientConfiguration.txt if defined
#<COPY_BridgeClientConfiguration>

# set container user
#<USER_SET>

# Set entrypoint
CMD ["./start-bridgeclient.sh"]
