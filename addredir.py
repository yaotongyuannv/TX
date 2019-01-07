# coding=utf-8
"""
增加redir的映射
"""
import os

import click
import requests
from dicom import read_file

from lib.dicom_ import tag_name2locator, get_named_tag_value
from lib.logger_ import get_logger
from lib.os_ import mkdir_recursive
from lib.project import get_project_root

cur_dir = os.path.join(get_project_root(), 'cmd/addredir/')

logger = get_logger('addredir')


@click.command('txaddredir', short_help=u'增加redir映射')
@click.option('-s', '--siuid', default='', help=u'检查UID')
@click.option('-d', '--display_id', default='', help=u'医生端显示UID')
@click.option('-f', '--dcm', type=click.Path(dir_okay=False), help=u'dcm文件路径')
@click.option('-t', '--tag', default='', help=u'dcm文件中用于跳转的标签')
@click.option('-L', '--log_dir', type=click.Path(file_okay=False),
              help=u'日志存储文件夹',
              default=os.path.join(cur_dir, 'log'), show_default=True)
def add_redir(siuid, display_id, dcm, tag, log_dir):
    """
    增加redir跳转关联, 两种方式:\n
      1. 通过 dicom文件路径 + 关联标签的方式 , 即需要定义 -f 和-t两个参数 \n
      2. 直接关联 study_instance_uid + 医生识别的ID, 即需要定义 -s 和-d两个参数\n
    """
    mkdir_recursive(log_dir)
    get_logger('addredir', level='INFO',
               path=os.path.join(log_dir, 'addredir.log'), backupCount=10,
               maxBytes=10 << 20)
    get_logger('addredir', level='ERROR',
               path=os.path.join(log_dir, 'addredir.err.log'), backupCount=10,
               maxBytes=10 << 20)
    logger.info('calling siuid: %s display_id: %s dcm: %s tag: %s' %
                (siuid, display_id, dcm, tag))
    if siuid and display_id:
        _add_redir(siuid, display_id)
    elif dcm and tag:
        try:
            tag_name2locator(tag)
        except ValueError:
            logger.error(u'不支持的tag类型: %s' % tag)
        try:
            dcm = read_file(dcm)
        except:
            logger.exception(u'打开dicom文件错误: %s' % dcm)

        siuid = dcm.StudyInstanceUID
        display_id = get_named_tag_value(dcm, tag)
        _add_redir(siuid, display_id)
    else:
        logger.error("命令错误, 要么siuid和display必传, 要么dcm和tag必传")


def _add_redir(siuid, display_id):
    """
    添加display_id到siuid的跳转
    :param siuid:检查uid
    :param display_id: 显示id
    :return:
    """
    try:
        resp = requests.post('http://localhost:3600/mapping/%s' % display_id,
                             json={"study_ids": [siuid]})
        logger.info('sent mapping signal: %s -> %s status: %s' %
                    (siuid, display_id, resp.status_code))
    except:
        logger.error('sent mapping signal error: %s -> %s' %
                     (siuid, display_id))


if __name__ == '__main__':
    add_redir()
