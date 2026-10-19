/* Minimal melt for the Kdenlive AppImage, which bundles libmlt but not the melt CLI.
 * Usage: kdenlive_melt [-quiet] PROJECT -consumer SERVICE:TARGET [name=value ...]
 * Loads PROJECT (a .kdenlive / MLT XML file) with the bundled MLT and renders it to the consumer.
 */
#include <framework/mlt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    const char *project = NULL, *consumer_arg = NULL;
    int i = 1;
    if (i < argc && !strcmp(argv[i], "-quiet"))
        i++;
    if (i < argc)
        project = argv[i++];
    if (i + 1 < argc && !strcmp(argv[i], "-consumer")) {
        consumer_arg = argv[i + 1];
        i += 2;
    }
    if (!project || !consumer_arg) {
        fprintf(stderr, "usage: %s [-quiet] PROJECT -consumer SERVICE:TARGET [name=value ...]\n", argv[0]);
        return 2;
    }
    mlt_factory_init(NULL);
    fprintf(stderr, "MLT %s\n", mlt_version_get_string());

    // A non-explicit profile is replaced by the project's own <profile>.
    mlt_profile profile = mlt_profile_init(NULL);
    mlt_producer producer = mlt_factory_producer(profile, "xml", project);
    if (!producer) {
        fprintf(stderr, "failed to load %s\n", project);
        return 1;
    }
    char service[64] = {0};
    const char *colon = strchr(consumer_arg, ':');
    strncpy(service, consumer_arg, colon ? (size_t)(colon - consumer_arg) : sizeof(service) - 1);
    mlt_consumer consumer = mlt_factory_consumer(profile, service, colon ? colon + 1 : NULL);
    if (!consumer) {
        fprintf(stderr, "failed to create consumer %s\n", service);
        return 1;
    }
    mlt_properties props = MLT_CONSUMER_PROPERTIES(consumer);
    for (; i < argc; i++) {
        if (!strncmp(argv[i], "out=", 4))
            mlt_producer_set_in_and_out(producer, 0, atoi(argv[i] + 4));
        else
            mlt_properties_parse(props, argv[i]);
    }
    mlt_properties_set_int(props, "terminate_on_pause", 1);
    fprintf(stderr, "%dx%d @ %d/%d fps, %d frames\n", profile->width, profile->height,
            profile->frame_rate_num, profile->frame_rate_den, mlt_producer_get_playtime(producer));

    mlt_consumer_connect(consumer, MLT_PRODUCER_SERVICE(producer));
    mlt_consumer_start(consumer);
    int last = -1;
    while (!mlt_consumer_is_stopped(consumer)) {
        int pos = mlt_producer_position(producer);
        if (pos / 100 != last / 100)
            fprintf(stderr, "frame %d\n", pos);
        last = pos;
        sleep(1);
    }
    mlt_consumer_close(consumer);
    mlt_producer_close(producer);
    mlt_profile_close(profile);
    mlt_factory_close();
    return 0;
}
