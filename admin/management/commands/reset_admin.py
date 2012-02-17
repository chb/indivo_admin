from django.core.management.base import NoArgsCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import User
from optparse import make_option
from django.conf import settings

class Command(NoArgsCommand):
    args = ''
    help = 'Resets the admin app to its initial state, recreating the default users specified in settings.py'

    option_list=NoArgsCommand.option_list + (
        make_option('--no-users',
                    action='store_false',
                    dest='add_users',
                    default=True,
                    help="Don't create the default users when performing the reset"),
        )

    def handle_noargs(self, **options):
        verbosity = int(options['verbosity'])

        # sync the database
        if verbosity:
            print "Syncing the Database..."
        call_command('syncdb', interactive=False)
        if verbosity:
            print "Done."

        # flush the database
        if verbosity:
            print "Flushing the Database..."
        call_command('flush', interactive=False, verbosity=verbosity)
        if verbosity:
            print "Done."

        # create the default users
        if options['add_users'] and settings.CREATE_USERS:
            if verbosity:
                print "Creating Default Users..."

            for user_data in settings.DEFAULT_USERS:
                fullname, email, username, password = user_data

                if verbosity:
                    print "\tCreating user %s"%username

                try:
                    user = User.objects.create_user(username, email, password)
                    user.is_superuser = True
                    name_bits = fullname.strip().split(' ')
                    user.first_name = name_bits[0]
                    user.last_name = name_bits[-1]
                    user.save()
                except Exception as e:
                    if verbosity:
                        print "Error creating user: %s"%str(e)

            if verbosity:
                print "Done."
