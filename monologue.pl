#!/usr/bin/perl
# A flood/monologue enforcing bot, kicks flooders and people who monologue too much
# Copyright (C) 2011  Daniel Kuehn, e-mail daniel@kuehn.se
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
use strict;
use warnings;
use 5.010;
use POE qw(Component::IRC);
use POE::Component::IRC::Plugin::Connector;
use Time::HiRes qw(time);

my ($irc)        = POE::Component::IRC->spawn() or die "Uhm, what the hell?! $!";
my %storage_hash = (
    curr_talker => 'none', 
    flood       => 0, 
    old_time    => time(),
    );
my %config = ();

POE::Session->create(inline_states => {
    _start     => \&bot_start, 
    irc_001    => \&on_connect, 
    irc_public => \&on_public,
    }
    );

sub bot_start {
    if (&set_config_options($ARGV[0])) {
	say 'Config is okay. Continuing with startup';
    } else {
	say 'You have too few/many config options, double check your configuration';
	exit(1);
    }
    $_[KERNEL]->state ('irc_disconnected' => \&irc_disconnected);
    $irc->yield(register => "all");
    $irc->yield(connect => {
	Nick     => $config{'nick'},
	Username => 'Monologue/Flood protection bot V0.2.2',
	Ircname  => $config{'ircname'},
	Server   => $config{'server'},
	Port     => $config{'port'},
	}	
        );
    my $plugin_reconnect = POE::Component::IRC::Plugin::Connector->new(delay => '120', reconnect => '180');
    $irc->plugin_add('Reconnect_plugin', $plugin_reconnect);
}

sub on_connect {
    my $login = "IDENTIFY".$config{'irc_password'};
    $irc->yield(privwsg => "NickServ", $login);
    $irc->yield(join => $config{'channels'});
    my $greeting = 'Sir, Ready for duty, Sir!';
    $irc->yield(privmsg => $config{'channels'}, $greeting);
}

sub irc_disconnected {
    say 'Shutting down...';
    $irc->plugin_del('Reconnect_plugin');
    $irc->yield(unregister => "all");
    exit(0);
}

sub on_public {
    my ($kernel, $who, $where, $msg) = @_[KERNEL, ARG0, ARG1, ARG2];
    my @nick                         = (split /[!|@]/, $who);
    my $channel                      = \$where->[0];
    my $ts                           = scalar localtime;
    $storage_hash{'time'}            = time();
    chomp($msg);
#    say 'Current talker(outside): '.$test_talker;
    
    &mono_flood_protection($nick[0], $$channel);
    &handle_messages($nick[0], $$channel, $msg);
    
#    say 'Current talker(outside): '.$test_talker;
}

sub mono_flood_protection {
    my ($nick,$chan)  = @_;
    
    if ($storage_hash{'curr_talker'} eq 'none') {
	$storage_hash{'curr_talker'} = $nick;
    }
#    say 'Nick: '.$nick,' Channel: '.$chan.' Talker: '.$talker;
    
    if ($storage_hash{'curr_talker'} ne $nick) {
	$storage_hash{'curr_talker'} = $nick;
	$storage_hash{$chan}   = 1;
	$storage_hash{'flood'} = 0;
#	say 'Nick: '.$storage_hash{'curr_talker'}.' Monologue: '.$storage_hash{$chan}.' Flood: '.$storage_hash{'flood'};
    } else {
	++$storage_hash{$chan};
#	say 'Nick: '.$storage_hash{'curr_talker'}.' Monologue: '.$storage_hash{$chan}.' Flood: '.$storage_hash{'flood'};
	
	my $diff     = $storage_hash{'time'}-$storage_hash{'old_time'};
#	say 'Diff: '.$diff;
	if ($diff < 2.6) {
	    ++$storage_hash{'flood'};
#	    say 'Flood: '.$storage_hash{'flood'};
	} else {
	    $storage_hash{'flood'} = 0;
#	    say 'No Flood: '.$storage_hash{'flood'};
	}
	
	$storage_hash{'old_time'} = $storage_hash{'time'};
    }
#    say 'Current talker: '.$storage_hash{'curr_talker'};
    if ($storage_hash{$chan} > $config{'monologue_limit'}) {
	$storage_hash{$chan} = 0;
	my $msg_to_user = $config{'monologue_kick_msg'};
#	$irc->yield(privmsg => $chan, $msg_to_user);
	$irc->yield(kick => $chan, $storage_hash{'curr_talker'}, $msg_to_user);
    }

    if ($storage_hash{'flood'} > $config{'flood_limit'}) {
	$storage_hash{$chan} = 0;
	my $msg_to_user = $config{'flood_kick_msg'};
	$storage_hash{'flood'} = 0;
#	$irc->yield(privmsg => $chan, $msg_to_user);
	$irc->yield(kick => $chan, $storage_hash{'curr_talker'}, $msg_to_user);
    }
#    say 'Current talker: '.$storage_hash{'curr_talker'];
}

sub handle_messages {
    my ($nick,$chan,$msg) = @_;
#    say "I reached the message handling Nick: ".$nick." Channel: ".$chan. " Msg: ".$msg;
    
#    if ($msg =~ /^!exit$/) {
#	say "I reached the exit function";
#	if (&allowed_to_shutdown($nick)) {
#	    my $exit = "Goodbye everyone! My master says its time to sleep";
#	    $irc->yield(quit => $exit);
#	} else {
#	    my $exit = "You are not my master, fu! >:(";
#	    $irc->yield(privmsg => $chan, $exit);
#	} 
#    }
    if ($msg =~ /^!author$/) {
#	say "I reached the author function";
	my $author = "Monologue bot V0.2.1, created by lejonet @ freenode and OFTC irc";
	$irc->yield(privmsg => $chan, $author);
    }
    if ($msg =~ /^!source$/) {
#	say "I reached the source function";
	my $source = "The sources are available at lejonet's github here: https://github.com/lejonet/Personal-projects/blob/master/ircbot.pl";
	$irc->yield(privmsg => $chan, $source);
    }
}

#sub allowed_to_shutdown {
#    my ($nick) = @_;
#    my $access = 0;
 #   say 'Nick: '.$nick;
#    foreach($config{'whitelist'}) {
#	if (&sanitize_input($_)) {
#	    say 'Nick from file: '.$_;
#	    if ($_ eq $nick) {
#		$access = 1;
#	    } else {
#		$access = 0;
#	    }
#	} else {
#	    say 'Untrusted characters in the input, you are not allowed to use anything but alphanumeric characters and _';
#	    exit(1);
#	}
#    }
#    if ($access == 1) {
#	return 1;
#    } else {
#	return 0;
#    }
#}

sub set_config_options {
    my $config_path = 'monologue.conf';
    if (defined($_[0])) {
	($config_path) = @_;
    } 
    say 'Config_path: '.$config_path;
    open(CONFIG, '<', $config_path) or die "Could not open file: $!";
    my @config_file = <CONFIG>;
    foreach (@config_file) {
	my @input = split(/=/, $_);
	@input    = &trim(@input);
	if (&sanitize_input(@input)) {
#	    say 'Input[0]: '.$input[0].' Input[1]: '.$input[1];
	    given ($input[0]) {
		when (/^nick$/) {
		    $config{'nick'}               = $input[1];
		}
		when (/^ircname$/) {
		    $config{'ircname'}            = $input[1];
		}
		when (/^server$/) {
		    $config{'server'}             = $input[1];
		}
		when (/^port$/) {
		    $config{'port'}               = $input[1];
		}
		when (/^monologue_limit$/) {
		    $config{'monologue_limit'}    = $input[1]
		}
		when (/^monologue_kick_msg$/) {
		    $config{'monologue_kick_msg'} = $input[1];
		}
		when (/^flood_limit$/) {
		    $config{'flood_limit'}        = $input[1];
		}
		when (/^flood_kick_msg$/) {
		    $config{'flood_kick_msg'}     = $input[1]; 
		}
		when (/^channels$/) {
		    $config{'channels'}           = $input[1];
		}
#		when (/^whitelist$/) {
#		    $config{'whitelist'}          = $input[1];
#		}
		when (/^irc_password$/) {
		    $config{'irc_password'}       = $input[1];
		}
		when (/^#/) {
		    ;
		}
		default {
		    say "Invalid configuration option: $input[0] = $input[1]";
		    exit(1);
		}
	    }
	} else {
	    say 'Untrusted characters in the input, you are not allowed to use anything but alphanumeric characters and some special characters like -_? and !';
	    exit(1);
	}
    }
	my $config_option_count = scalar keys %config;
	if ($config_option_count == 10) {
	    return 1;
	} else {
	    return 0;
	}	    
}

sub sanitize_input {
    my @untrusted = @_;
    my $trusted   = 0;
#    say 'Untrusted: '.@untrusted;
    foreach (@untrusted) {
#	say 'In loop: '.$_;
	if ($_ =~ m/[a-zA-Z0-9\_\?\!\-\#\s']{1,512}/) {
	    $trusted = 1;
	} else {
	    $trusted = 0;
	}
    }
#    say 'Trusted: '.$trusted;
    if ($trusted == 1) {
	return 1;
    } else {
	return 0;
    }
}

sub trim {
    my (@string) = @_;
    foreach (@string) {
	$_ =~ s/^\s+//;
	$_ =~ s/\s+$//;
    }
    return @string;
}

$poe_kernel->run();
exit(0);
